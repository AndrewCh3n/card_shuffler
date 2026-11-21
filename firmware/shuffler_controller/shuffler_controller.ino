/*
 * Programmable Playing Card Shuffler - Motion & Sensor Controller
 * Target: Arduino Nano / Arduino Uno (ATmega328P)
 *
 * Dependencies (install via Arduino Library Manager):
 *   - AccelStepper (by Mike McCauley)
 *   - Servo (built into Arduino IDE)
 *
 * Pinout & serial protocol match docs/architecture.md and docs/cad_spec.md.
 * Baud rate: 115200 8N1, newline-terminated uppercase ASCII commands.
 */

#include <AccelStepper.h>
#include <Servo.h>
#include <stdlib.h>
#include <string.h>

// ============================================================================
// Pin Assignments (ATmega328P - Nano / Uno)
// ============================================================================
constexpr uint8_t PIN_ELEV_STEP       = 2;   // TMC2209 #1 STEP (Elevator)
constexpr uint8_t PIN_ELEV_DIR        = 3;   // TMC2209 #1 DIR
constexpr uint8_t PIN_ELEV_EN         = 4;   // TMC2209 #1 EN (Active LOW)

constexpr uint8_t PIN_FEED_STEP       = 5;   // TMC2209 #2 STEP (Feeder)
constexpr uint8_t PIN_FEED_DIR        = 6;   // TMC2209 #2 DIR
constexpr uint8_t PIN_FEED_EN         = 7;   // TMC2209 #2 EN (Active LOW)

constexpr uint8_t PIN_ELEV_HOME_SW    = 8;   // Bottom limit switch (Active LOW)
constexpr uint8_t PIN_COMB_SERVO      = 9;   // MG90S servo (Timer1 PWM)
constexpr uint8_t PIN_SCAN_LED_PWM    = 11;  // White scan LEDs MOSFET (Timer2 PWM; D10 avoided due to Servo)
constexpr uint8_t PIN_HOPPER_SENS     = 12;  // TCRT5000 hopper card-present sensor (Active LOW)
constexpr uint8_t PIN_SCAN_ENTRY_SENS = A0;  // IR sensor: card staged over camera window (Active LOW)
constexpr uint8_t PIN_SLOT_EXIT_SENS  = A1;  // IR sensor: card clearing into elevator slot (Active LOW)

// ============================================================================
// Mechanical Calibration Constants (Match docs/cad_spec.md)
// ============================================================================
constexpr int   NUM_SLOTS             = 54;    // 52 cards + 2 Jokers (slots 0..53)
constexpr long  ELEV_STEPS_PER_MM     = 400;   // NEMA17 200*16 microsteps / 8 mm T8x8 lead = 400 steps/mm
constexpr long  SLOT_PITCH_MM         = 2;     // 2.0 mm slot pitch
constexpr long  STEPS_PER_SLOT        = ELEV_STEPS_PER_MM * SLOT_PITCH_MM;  // 800 steps/slot
constexpr long  ELEV_MAX_STEPS        = (NUM_SLOTS - 1L) * STEPS_PER_SLOT;  // 42,400 steps (106 mm)

// Stepper speed / acceleration tuning (steps/sec and steps/sec^2)
constexpr float ELEV_MAX_SPEED        = 12000.0f;  // ~30 mm/s (~3.5s full sweep, ~1.1s avg hop)
constexpr float ELEV_ACCEL            = 24000.0f;
constexpr float ELEV_HOME_SPEED       = -4000.0f;  // Slow downward seek toward bottom switch
constexpr unsigned long HOME_TIMEOUT_MS = 12000UL;

// Feeder kinematics (25 mm OD silicone wheel => ~78.5 mm/rev => ~40.7 steps/mm @ 16x microstep)
constexpr float FEED_MAX_SPEED        = 5000.0f;   // ~120 mm/s card feed velocity
constexpr float FEED_ACCEL            = 16000.0f;
constexpr long  FEED_TO_SCAN_MAX_STEPS = 4200L;    // ~103 mm safety limit before declaring misfeed
constexpr long  EJECT_CLEAR_MAX_STEPS  = 4800L;    // ~118 mm safety limit before declaring jam
constexpr long  EJECT_EXTRA_PUSH_STEPS = 400L;     // ~10 mm extra nudge to seat card fully in slot
constexpr long  NUDGE_LIMIT_STEPS      = 2000L;

// Expanding-comb servo angles (tune on Bench Test A linkage!)
constexpr int   COMB_CLOSED_DEG       = 20;
constexpr int   COMB_OPEN_DEG         = 110;
constexpr unsigned long COMB_SETTLE_MS = 350UL;

// Sensor polarity (true = LOW means triggered/card detected)
constexpr bool  SENSOR_ACTIVE_LOW     = true;

// ============================================================================
// Globals
// ============================================================================
AccelStepper elevStepper(AccelStepper::DRIVER, PIN_ELEV_STEP, PIN_ELEV_DIR);
AccelStepper feedStepper(AccelStepper::DRIVER, PIN_FEED_STEP, PIN_FEED_DIR);
Servo combServo;

bool isHomed        = false;
int  currentSlot    = NUM_SLOTS - 1;  // At bottom home (Z=0), slot 53 aligns with feed plane
bool combIsOpen     = false;

char cmdBuf[64];
uint8_t cmdIdx = 0;

// ============================================================================
// Helper Functions
// ============================================================================
inline bool readSensorTriggered(uint8_t pin) {
  bool level = (digitalRead(pin) == HIGH);
  return SENSOR_ACTIVE_LOW ? !level : level;
}

void enableSteppers(bool enable) {
  // TMC2209 EN pin is active LOW
  uint8_t val = enable ? LOW : HIGH;
  digitalWrite(PIN_ELEV_EN, val);
  digitalWrite(PIN_FEED_EN, val);
}

void setCombOpen(bool open) {
  combServo.write(open ? COMB_OPEN_DEG : COMB_CLOSED_DEG);
  combIsOpen = open;
  delay(COMB_SETTLE_MS);
}

/*
 * Kinematic mapping (docs/cad_spec.md):
 *   Bottom home (Z = 0 steps) aligns physical slot 53 with the fixed feed plane
 *   and places physical slot 0 just 2 mm above the output catcher tray.
 *   To align physical slot `slot` (0..53) with the feed plane:
 *     targetSteps = (53 - slot) * 800
 */
long slotToSteps(int slot) {
  return (long)(NUM_SLOTS - 1 - slot) * STEPS_PER_SLOT;
}

// ============================================================================
// Motion Actions
// ============================================================================
void handleHome() {
  setCombOpen(false);
  enableSteppers(true);

  // If already pressing the switch, back off slightly first for repeatable homing
  if (readSensorTriggered(PIN_ELEV_HOME_SW)) {
    elevStepper.setCurrentPosition(0);
    elevStepper.moveTo(STEPS_PER_SLOT * 2L);  // +4 mm upward
    while (elevStepper.distanceToGo() != 0) {
      elevStepper.run();
    }
  }

  // Seek downward until home switch triggers
  elevStepper.setSpeed(ELEV_HOME_SPEED);
  unsigned long startMs = millis();
  while (!readSensorTriggered(PIN_ELEV_HOME_SW)) {
    elevStepper.runSpeed();
    if (millis() - startMs > HOME_TIMEOUT_MS) {
      enableSteppers(false);
      isHomed = false;
      Serial.println(F("ERR HOME_TIMEOUT Elevator did not reach bottom switch"));
      return;
    }
  }

  elevStepper.setCurrentPosition(0);
  isHomed = true;
  currentSlot = NUM_SLOTS - 1;  // Slot 53 aligned with feed plane; slot 0 at output tray
  Serial.println(F("OK HOMED"));
}

void handleMoveSlot(int slot) {
  if (!isHomed) {
    Serial.println(F("ERR NOT_HOMED Run HOME before MOVE_SLOT"));
    return;
  }
  if (slot < 0 || slot >= NUM_SLOTS) {
    Serial.println(F("ERR BAD_SLOT Slot must be 0..53"));
    return;
  }
  if (combIsOpen) {
    setCombOpen(false);
  }

  enableSteppers(true);
  long target = slotToSteps(slot);
  elevStepper.moveTo(target);
  while (elevStepper.distanceToGo() != 0) {
    elevStepper.run();
  }

  currentSlot = slot;
  Serial.print(F("OK SLOT="));
  Serial.println(currentSlot);
}

void handleFeedToScan() {
  if (!readSensorTriggered(PIN_HOPPER_SENS)) {
    Serial.println(F("ERR HOPPER_EMPTY No cards detected in input hopper"));
    return;
  }

  enableSteppers(true);
  feedStepper.setCurrentPosition(0);
  feedStepper.moveTo(FEED_TO_SCAN_MAX_STEPS);

  while (feedStepper.distanceToGo() != 0) {
    feedStepper.run();
    if (readSensorTriggered(PIN_SCAN_ENTRY_SENS)) {
      feedStepper.setCurrentPosition(feedStepper.currentPosition());
      Serial.println(F("OK AT_SCAN"));
      return;
    }
  }

  Serial.println(F("ERR FEED_TIMEOUT Card did not reach scan sensor"));
}

void handleEjectToSlot() {
  enableSteppers(true);
  feedStepper.setCurrentPosition(0);
  feedStepper.moveTo(EJECT_CLEAR_MAX_STEPS);

  bool sawCardAtExit = readSensorTriggered(PIN_SLOT_EXIT_SENS);

  while (feedStepper.distanceToGo() != 0) {
    feedStepper.run();
    bool exitTrig = readSensorTriggered(PIN_SLOT_EXIT_SENS);

    if (exitTrig) {
      sawCardAtExit = true;
    } else if (sawCardAtExit && !exitTrig) {
      // Trailing edge just cleared the exit sensor -> small extra push to seat card cleanly
      long seatTarget = feedStepper.currentPosition() + EJECT_EXTRA_PUSH_STEPS;
      feedStepper.moveTo(seatTarget);
      while (feedStepper.distanceToGo() != 0) {
        feedStepper.run();
      }
      Serial.println(F("OK EJECTED"));
      return;
    }
  }

  Serial.println(F("ERR JAM_DETECTED Card did not clear slot exit sensor"));
}

void handleNudgeFeed(long steps) {
  if (steps < -NUDGE_LIMIT_STEPS || steps > NUDGE_LIMIT_STEPS) {
    Serial.println(F("ERR BAD_ARG Nudge steps out of range"));
    return;
  }
  enableSteppers(true);
  feedStepper.setCurrentPosition(0);
  feedStepper.moveTo(steps);
  while (feedStepper.distanceToGo() != 0) {
    feedStepper.run();
  }
  Serial.println(F("OK NUDGED"));
}

void handleStatus() {
  Serial.print(F("OK SLOT="));
  Serial.print(currentSlot);
  Serial.print(F(" HOMED="));
  Serial.print(isHomed ? 1 : 0);
  Serial.print(F(" HOPPER="));
  Serial.print(readSensorTriggered(PIN_HOPPER_SENS) ? 1 : 0);
  Serial.print(F(" SCAN="));
  Serial.print(readSensorTriggered(PIN_SCAN_ENTRY_SENS) ? 1 : 0);
  Serial.print(F(" EXIT="));
  Serial.print(readSensorTriggered(PIN_SLOT_EXIT_SENS) ? 1 : 0);
  Serial.print(F(" COMB="));
  Serial.println(combIsOpen ? F("OPEN") : F("CLOSED"));
}

// ============================================================================
// Command Parser
// ============================================================================
void processCommand(char* line) {
  // Trim trailing whitespace/CR
  size_t len = strlen(line);
  while (len > 0 && (line[len - 1] == '\r' || line[len - 1] == ' ' || line[len - 1] == '\t')) {
    line[--len] = '\0';
  }
  if (len == 0) return;

  if (strcmp(line, "PING") == 0) {
    Serial.println(F("OK PONG"));
  } else if (strcmp(line, "STATUS") == 0) {
    handleStatus();
  } else if (strcmp(line, "HOME") == 0) {
    handleHome();
  } else if (strncmp(line, "MOVE_SLOT ", 10) == 0) {
    char* endPtr = nullptr;
    long slot = strtol(line + 10, &endPtr, 10);
    if (endPtr == line + 10 || *endPtr != '\0') {
      Serial.println(F("ERR BAD_SLOT Invalid integer slot argument"));
    } else {
      handleMoveSlot((int)slot);
    }
  } else if (strcmp(line, "FEED_TO_SCAN") == 0) {
    handleFeedToScan();
  } else if (strcmp(line, "EJECT_TO_SLOT") == 0) {
    handleEjectToSlot();
  } else if (strncmp(line, "NUDGE_FEED ", 11) == 0) {
    char* endPtr = nullptr;
    long steps = strtol(line + 11, &endPtr, 10);
    if (endPtr == line + 11 || *endPtr != '\0') {
      Serial.println(F("ERR BAD_ARG Invalid integer nudge argument"));
    } else {
      handleNudgeFeed(steps);
    }
  } else if (strcmp(line, "COMB_OPEN") == 0) {
    setCombOpen(true);
    Serial.println(F("OK COMB_OPEN"));
  } else if (strcmp(line, "COMB_CLOSE") == 0) {
    setCombOpen(false);
    Serial.println(F("OK COMB_CLOSED"));
  } else if (strncmp(line, "LED ", 4) == 0) {
    int brightness = constrain(atoi(line + 4), 0, 255);
    analogWrite(PIN_SCAN_LED_PWM, brightness);
    Serial.print(F("OK LED="));
    Serial.println(brightness);
  } else if (strcmp(line, "DISABLE_MOTORS") == 0) {
    enableSteppers(false);
    Serial.println(F("OK DISABLED"));
  } else if (strcmp(line, "ESTOP") == 0) {
    elevStepper.stop();
    feedStepper.stop();
    enableSteppers(false);
    isHomed = false;
    Serial.println(F("OK ESTOP"));
  } else {
    Serial.print(F("ERR UNKNOWN_CMD "));
    Serial.println(line);
  }
}

// ============================================================================
// Setup & Main Loop
// ============================================================================
void setup() {
  Serial.begin(115200);

  pinMode(PIN_ELEV_EN, OUTPUT);
  pinMode(PIN_FEED_EN, OUTPUT);
  enableSteppers(false);

  pinMode(PIN_ELEV_HOME_SW, INPUT_PULLUP);
  pinMode(PIN_HOPPER_SENS, INPUT_PULLUP);
  pinMode(PIN_SCAN_ENTRY_SENS, INPUT_PULLUP);
  pinMode(PIN_SLOT_EXIT_SENS, INPUT_PULLUP);

  pinMode(PIN_SCAN_LED_PWM, OUTPUT);
  analogWrite(PIN_SCAN_LED_PWM, 0);

  elevStepper.setMaxSpeed(ELEV_MAX_SPEED);
  elevStepper.setAcceleration(ELEV_ACCEL);
  // Flip setPinsInverted(true, false, false) if your leadscrew moves opposite to expected!

  feedStepper.setMaxSpeed(FEED_MAX_SPEED);
  feedStepper.setAcceleration(FEED_ACCEL);

  combServo.attach(PIN_COMB_SERVO);
  setCombOpen(false);

  Serial.println(F("OK READY SHUFFLER_FW_V1"));
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      cmdBuf[cmdIdx] = '\0';
      processCommand(cmdBuf);
      cmdIdx = 0;
    } else if (cmdIdx < sizeof(cmdBuf) - 1) {
      cmdBuf[cmdIdx++] = c;
    }
  }
}
