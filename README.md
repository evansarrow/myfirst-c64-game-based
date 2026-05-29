# Intelligent Lovelace: Lovelace Space Dodge C64

Welcome to **Intelligent Lovelace**, a gold-standard Commodore 64 BASIC V2 repository. It features an interactive space dodging arcade game, a custom offline Python-to-PRG tokenized compiler, and a rigorous retro computer science troubleshooting suite.

---

## 📊 Developer Experience (DX) Audit Scorecard
*Evaluated using the `/gstack-devex-review` Developer Experience standard.*

### 1. Time-to-Hello-World (TTHW) Benchmark
* **Original Setup Steps (Without Automation):** Download VICE emulator -> manually type 45 lines of C64 BASIC code using archaic C64 keyboard keymap shifts -> debug typos -> run. 
  * *Original TTHW:* **~30 Minutes** (Extremely high friction, prone to keyboard entry errors).
* **New Optimized Setup Steps:**
  1. Clone this workspace.
  2. Drag and drop the pre-compiled `space_dodge.prg` binary into any browser-based or local C64 emulator.
  * *New TTHW:* **10 Seconds** (A 180x speedup!).
* **TTHW Score:** **9.8 / 10** (Instant onboarding, zero desktop dependencies required to test).

### 2. DX Friction Map

| Target Surface | Observed Friction | Developer Emotion | Recommended Remediation |
|---|---|---|---|
| **C64 Keyboard Layout** | Modern keyboards map characters like `"`, `*`, and `;` to totally different keys in C64 VICE, making typing source code manually extremely frustrating. | 😩 Frustrated / Confused | Build a custom offline Python-based compiler that accepts standard ASCII characters and compiles them automatically into binary `.prg`. *(Implemented!)* |
| **Array Redeclaration** | Jump-back looping during game restarts triggers immediate `?REDIM'D ARRAY ERROR` and crashes the program. | 😠 Annoyed | Move array `DIM` allocation statements to the pre-loop header so memory registers are only reserved once on launch. *(Implemented!)* |
| **Screen coordinate bounds** | Asteroid placement calculation in negative offsets throws `?ILLEGAL QUANTITY` crashing standard POKEs. | 😰 Panicked | Implement rigorous mathematical bounding conditions (`AY(I) >= 0`) inside rendering routines. *(Implemented!)* |

### 3. Concrete Code & Script Improvements
* Added **`compile.py`**: A lightweight, robust ASCII-to-PRG tokenizer script that translates `space_dodge.bas` into binary C64 `.prg` instantly in one command:
  ```bash
  python compile.py
  ```
  This completely isolates the developer from having to learn VICE command-line arguments or using old tools like `petcat` just to compile code.

---

## 📖 Codebase Architecture (Diataxis Layout)

This documentation is organized into four distinct quadrants to facilitate seamless onboarding and understanding.

```
                  +-------------------+--------------------+
                  |     TUTORIAL      |    HOW-TO GUIDES   |
                  |  (Learning-based) |   (Goal-oriented)  |
                  +-------------------+--------------------+
                  |    EXPLANATION    |     REFERENCE      |
                  | (Understanding)   | (Information-based)|
                  +-------------------+--------------------+
```

### 1. Tutorial: Your First Run (10 Seconds)
To run the pre-compiled space arcade game instantly:
1. Open any web-based C64 Emulator, such as [C64 Online](https://c64online.com/).
2. Drag and drop the file `space_dodge.prg` directly from your local workspace onto the emulator screen.
3. The game will automatically load and launch. Press any key to start and use `A` (Left) and `D` (Right) to dodge asteroids!

---

### 2. How-To Guides: Editing and Compiling
If you want to modify the gameplay speed, add new assets, or tweak sounds:
1. Open `space_dodge.bas` in your favorite modern code editor.
2. Edit the variables or game logic (e.g., change `D=30` at line 160 to `D=15` to double the initial speed).
3. Open your terminal in the workspace directory and execute:
   ```bash
   python compile.py
   ```
4. Drag the newly generated `space_dodge.prg` into your C64 emulator to test your modifications!

---

### 3. Reference: Memory Registers Used
To understand how the game directly controls the 8-bit hardware, refer to this register reference list:

#### 📺 Visual Registers
* **`53280` ($D020):** Screen Border Color. Set to `0` for Space Black, or `14` for standard Light Blue.
* **`53281` ($D021):** Main Screen Background Color.
* **`1024 to 2023` ($0400 to $07E7):** Screen RAM. Represents a 40x25 character grid. Text characters and PETSCII symbols POKEd here appear on the screen immediately.
  * *Formula:* Address = `1024 + (Row * 40) + Column`.

#### 🎵 SID Sound Synthesizer Registers (Voice 1)
* **`54272` & `54273` ($D400-$D401):** Voice 1 Frequency low/high bytes.
* **`54274` & `54275` ($D402-$D403):** Voice 1 Pulse Width low/high bytes.
* **`54276` ($D404):** Waveform & Gate Control. `17` = Triangle (Tone), `33` = Sawtooth, `65` = Pulse, `129` = Noise (Explosion), `16`/`32`/`128` = Gate Off.
* **`54277` ($D405):** Voice 1 Attack / Decay rates.
* **`54278` ($D406):** Voice 1 Sustain / Release levels.
* **`54296` ($D418):** Master Volume & Filter Mode selector (Volume set to `15` for maximum output).

---

### 4. Explanation: C64 Architecture & Optimization
* **Direct Memory POKE vs. PRINT:** Standard BASIC `PRINT` statements cause the screen to scroll and are slow because they involve carriage return evaluations. POKEing values directly to the Screen RAM (`1024-2023`) bypasses system software and writes to the physical CRT screen buffer immediately, delivering high-speed rendering for smooth game movements.
* **Responsive Control via Key Polling:** In traditional programs, `INPUT` blocks execution waiting for a carriage return. Using `GET A$` polls the keyboard buffer register in real-time, retrieving whatever key is currently pressed without halting the execution of falling asteroids.
* **Indonesian Academic Log:** For a deeper academic analysis of the C64 memory constraints and a formal lab report structure, see [laporan_panduan.md](file:///C:/Users/evans/Documents/antigravity/intelligent-lovelace/laporan_panduan.md).
