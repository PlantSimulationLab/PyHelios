# Native Documentation Synchronization Guide

**Purpose:** This guide helps future agents synchronize PyHelios plugin documentation with native Helios C++ documentation while maintaining 100% accuracy and consistency.

**Critical Philosophy:** PyHelios documentation should be **IDENTICAL** to native C++ documentation for all theoretical content (equations, theory, parameter tables, figures), but **PYTHON-SPECIFIC** for API examples, installation, and usage instructions.

---

## Why This Task Is Deceptively Difficult

**The Temptation:** Creating a "combined" document by cherry-picking sections seems faster.

**The Reality:** You **WILL** miss sections, skip equations, drop cross-references, and introduce subtle inconsistencies that break the documentation.

**The Solution:** Follow the proven workflow below with **ZERO DEVIATIONS**.

---

## Mandatory Pre-Flight Checks

Before starting ANY documentation synchronization:

### 1. Check Doxygen Configuration Consistency

```bash
# Compare MathJax settings
grep -A5 "USE_MATHJAX" docs/Doxyfile.python
grep -A5 "USE_MATHJAX" helios-core/doc/Doxyfile

# Compare HTML settings
grep -E "(HTML_HEADER|HTML_FOOTER|HTML_STYLESHEET)" docs/Doxyfile.python
grep -E "(HTML_HEADER|HTML_FOOTER|HTML_STYLESHEET)" helios-core/doc/Doxyfile
```

**Critical Settings That Must Match:**
- `USE_MATHJAX = YES` (for equation rendering)
- `MATHJAX_VERSION = MathJax_3`
- `MATHJAX_RELPATH = https://cdn.jsdelivr.net/npm/mathjax@3`

**If they don't match:** Fix Doxyfile.python FIRST before touching documentation.

### 2. Identify All Assets

```bash
# Find ALL figures, images, data files
find helios-core/plugins/PLUGINNAME/doc -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.svg" -o -name "*.dat" \)
```

**Action:** Note which assets need to be copied to `docs/images/`.

### 3. Read BOTH Documentation Files Completely

**DO NOT SKIP THIS STEP.** Read:
1. Native C++ doc (`.dox` file)
2. Existing PyHelios doc (`.md` file)
3. Backup PyHelios doc to identify PyHelios-specific sections

**Understand:**
- Which sections are pure theory (copy exactly)
- Which sections are API examples (convert to Python)
- Which sections are PyHelios-specific (preserve)

---

## The Proven 6-Step Workflow

### Step 1: Backup and Replace

**DO EXACTLY THIS, NO SHORTCUTS:**

```bash
# 1. Backup existing PyHelios doc
cp docs/plugin_PLUGINNAME.md docs/plugin_PLUGINNAME.md.backup

# 2. Copy native doc to REPLACE PyHelios doc
cp helios-core/plugins/PLUGINNAME/doc/PLUGINNAME.dox docs/plugin_PLUGINNAME.md
```

**Why this matters:** Starting with the EXACT native content guarantees you won't miss sections, equations, or references.

**Common mistakes to avoid:**
- ❌ Creating a new file and trying to "combine" sections
- ❌ Reading native doc and manually retyping content
- ❌ Copying "most" of the native doc but keeping some PyHelios sections

### Step 2: Convert Format Section-by-Section

**Work in this order, getting approval after EACH section:**

1. **Header and TOC**
2. **Primitive Data Tables**
3. **Model Theory Sections** (usually the longest)
4. **Usage Examples**
5. **PyHelios-Specific Sections** (Installation, Troubleshooting, etc.)

**Conversion Rules:**

| Doxygen Syntax | Markdown Syntax | Notes |
|----------------|-----------------|-------|
| `/*! \page PageID Title` | `# Title {#PageID}` | Remove comment markers |
| `\tableofcontents` | `[TOC]` | Doxygen markdown uses [TOC] |
| `\section SectionID Title` | `## Title {#SectionID}` | Preserve anchor IDs |
| `\subsection SubID Title` | `### Title {#SubID}` | Preserve anchor IDs |
| `\subsubsection SubSubID Title` | `#### Title {#SubSubID}` | Preserve anchor IDs |
| `~~~~~~~~{.cpp}` | ` ```cpp ` | Markdown fenced code blocks |
| `\ref ClassName` | `\ref pyhelios.Module.ClassName "ClassName"` | **MUST USE FULLY QUALIFIED** (see Python Reference Syntax below) |
| `\ref Class::method()` | `\ref pyhelios.Module.Class::method "method()"` | **MUST USE FULLY QUALIFIED** (see Python Reference Syntax below) |
| `\f$equation\f$` | `\f$equation\f$` | **KEEP AS-IS** (Doxygen LaTeX) |
| `\f[equation\f]` | `\f[equation\f]` | **KEEP AS-IS** (Doxygen LaTeX) |
| `<table>...</table>` | `<table>...</table>` | **KEEP AS-IS** (HTML works in markdown) |
| `<a href="...">text</a>` | `[text](url)` or keep HTML | Either works, be consistent |

**Critical Rules:**
- ✅ **NEVER** convert `\ref` to backticks - cross-references must use `\ref`
- ✅ **NEVER** convert `\f$` equations to plain text or markdown math
- ✅ **NEVER** simplify HTML tables to markdown tables (you'll break formatting)
- ✅ **NEVER** skip the "boring" parts like footnotes or disclaimers

**Python Reference Syntax (CRITICAL FOR HYPERLINKS):**

Doxygen requires **fully qualified names** for Python class and method references to create working hyperlinks:

```markdown
<!-- ❌ WRONG: Will show "unable to resolve reference" warnings -->
\ref PhotosynthesisModel
\ref FarquharModelCoefficients
\ref PhotosynthesisModel::run()

<!-- ✅ CORRECT: Use fully qualified names with display text -->
\ref pyhelios.PhotosynthesisModel.PhotosynthesisModel "PhotosynthesisModel"
\ref pyhelios.types.photosynthesis.FarquharModelCoefficients "FarquharModelCoefficients"
\ref pyhelios.PhotosynthesisModel.PhotosynthesisModel::run "run()"
\ref pyhelios.types.photosynthesis.FarquharModelCoefficients::setVcmax "setVcmax()"
```

**Format Pattern:**
- **For classes in main pyhelios/**: `\ref pyhelios.FileName.ClassName "ClassName"`
  - Example: `\ref pyhelios.PhotosynthesisModel.PhotosynthesisModel "PhotosynthesisModel"`
  - Example: `\ref pyhelios.StomatalConductance.StomatalConductanceModel "StomatalConductanceModel"`

- **For classes in pyhelios/types/**: `\ref pyhelios.types.modulename.ClassName "ClassName"`
  - Example: `\ref pyhelios.types.photosynthesis.FarquharModelCoefficients "FarquharModelCoefficients"`

- **For methods**: `\ref pyhelios.Module.ClassName::methodName "methodName()"`
  - Example: `\ref pyhelios.PhotosynthesisModel.PhotosynthesisModel::run "run()"`
  - Example: `\ref pyhelios.types.photosynthesis.FarquharModelCoefficients::setVcmax "setVcmax()"`

- **For other plugins**: `\ref pyhelios.PluginName.PluginNameModel "PluginNameModel"`
  - Example: `\ref pyhelios.RadiationModel.RadiationModel "RadiationModel"`
  - Example: `\ref pyhelios.EnergyBalance.EnergyBalanceModel "EnergyBalanceModel"`

**Why This Matters:**
- Short names like `\ref PhotosynthesisModel` cause "unable to resolve reference" warnings
- Automatic linking (no `\ref`) does NOT work for Python methods - they show as plain text
- Only fully qualified names create working hyperlinks in generated documentation
- Discovered during photosynthesis doc sync (2025-12-03) after systematic debugging

### Step 3: Replace C++ Code Examples with Python

**ONLY convert code blocks. NEVER touch:**
- Equations
- Tables
- Theory text
- References

**Code Conversion Checklist:**

```python
# C++ → Python conversions
helios::Context* → Context (as context manager)
StomatalConductanceModel(&context) → StomatalConductanceModel(context)
make_vec3(x,y,z) → vec3(x,y,z)
make_vec2(x,y) → vec2(x,y)
std::vector<uint> → list in Python
uint UUID → UUID (Python int)
context.getPrimitiveData(UUID, "label", var) → var = context.getPrimitiveData(UUID, "label")
std::cout << → print(f"...")
```

**Critical API Verification:**

Before writing ANY code example:
1. **Grep for the method** in PyHelios source:
   ```bash
   grep -rn "def methodName" pyhelios/
   ```
2. **Verify the signature** matches what you're documenting
3. **Test the import** works:
   ```python
   python -c "from pyhelios import ClassName"
   ```

**Common API Mistakes:**
- ❌ Using C++ method names that don't exist in Python
- ❌ Using material-based API when Python only has UUID-based
- ❌ Wrong parameter order or parameter names
- ❌ Missing required imports

### Step 4: Add PyHelios-Specific Sections

**CRITICAL: Standardized Front Matter Format**

PyHelios plugin documentation uses a **standardized front matter** that differs from native C++ Helios docs. The pattern established in photosynthesis and stomatal conductance docs is:

**Section Order (REQUIRED):**
1. Page header with anchor
2. [TOC]
3. **Metadata Table** (simplified - 3 rows only)
4. **System Requirements** (platform info)
5. **Quick Start** (minimal code example)
6. Then native content begins...

**Template (EXACT FORMAT TO USE):**

```markdown
# Plugin Name Documentation {#PluginNameDoc}

[TOC]

<table>
<tr><th>Dependencies</th><td>None (or list dependencies)</td></tr>
<tr><th>Python Import</th><td>`from pyhelios import PluginClassName`</td></tr>
<tr><th>Main Class</th><td>\ref pyhelios.ModuleName.PluginClassName "PluginClassName"</td></tr>
</table>

## System Requirements

<table>
  <tr>
    <th>Dependencies</th>
    <td>None (or list)</td>
  </tr>
  <tr>
    <th>Platforms</th>
    <td>Windows, Linux, macOS</td>
  </tr>
  <tr>
    <th>GPU</th>
    <td>Not required (or "Required - CUDA/OptiX")</td>
  </tr>
</table>

## Quick Start

\```python
from pyhelios import Context, PluginClassName
from pyhelios.types import vec3, vec2

with Context() as context:
    # Create minimal geometry
    uuid = context.addPatch(center=vec3(0, 0, 0), size=vec2(0.1, 0.1))

    # Set required primitive data (plugin-specific)
    context.setPrimitiveData(uuid, "some_data", value)

    # Use plugin
    with PluginClassName(context) as plugin:
        # Configure (use species library if available)
        plugin.setCoefficientsFromLibrary("SpeciesName")

        # Run
        plugin.run()

        # Get results
        result = context.getPrimitiveData(uuid, "output_data")
        print(f"Result: {result[0]}")
\```

## Class Constructor {#PluginConstructor}

<table>
<tr><th>Constructors</th></tr>
<tr><td>\ref pyhelios.ModuleName.PluginClassName "PluginClassName"</td></tr>
</table>

## Primitive Data {#PluginVarsAndProps}

(Begin native content here...)
```

**CRITICAL CHANGES FROM NATIVE:**

1. **Metadata Table (Lines 5-9):**
   - ❌ **REMOVE** from native: "CMakeLists.txt", "Header File" rows (C++ specific)
   - ✅ **KEEP**: "Dependencies" row
   - ✅ **ADD**: "Python Import" row with backtick code
   - ✅ **CHANGE**: "Class" → "Main Class" with fully qualified `\ref`

2. **Installation Section:**
   - ❌ **DO NOT ADD** "Installation" or "Build with PluginName" sections
   - **Rationale**: Build instructions are covered in main PyHelios documentation
   - **Exception**: Only add if plugin has special build requirements (unusual dependencies)

3. **Quick Start Section:**
   - ✅ **ALWAYS ADD** before native content
   - Must show minimal working example
   - Must use context manager pattern
   - Must import from `pyhelios.types`
   - Should demonstrate species library if available

4. **Section Placement:**
   - **Metadata table**: Immediately after [TOC]
   - **System Requirements**: After metadata table
   - **Quick Start**: After System Requirements
   - **Class Constructor**: After Quick Start (from native doc)
   - **Primitive Data**: After Constructor (from native doc)

**Where to place these:** At the TOP of the document, BEFORE the Class Constructor section from native docs.

### Step 5: Verify Cross-References and Hyperlinks

**Systematic verification checklist:**

```bash
# 1. Find all \ref references in your doc
grep -o '\\ref [A-Za-z_:]*' docs/plugin_PLUGINNAME.md | sort -u

# 2. For each reference, verify it exists
# Plugin references should match other plugin class names
# Method references should match actual PyHelios API
# Coefficient structure references should match Python classes
```

**Cross-Reference Categories:**

| Reference Type | Example | Verification |
|----------------|---------|--------------|
| Plugin classes | `\ref RadiationModel` | Check plugins/ directory |
| Coefficient structures | `\ref BMFcoefficients` | Check if exists in Python |
| Methods | `\ref StomatalConductanceModel::run` | Grep for "def run" |
| Internal sections | `\ref BMFTheory` | Check anchor exists in same doc |

**Critical Rules:**
- ✅ Plugin names use `\ref PluginName` for hyperlinking
- ✅ Method names use `\ref ClassName::methodName` for API docs
- ✅ Internal sections use `\ref AnchorID` for navigation
- ❌ **NEVER** use plain backticks for things that should be hyperlinked

### Step 6: Build and Verify

**Build command:**
```bash
cd docs
doxygen Doxyfile.python 2>&1 | tee build.log
```

**Check for issues:**
```bash
# Filter out known non-issues
grep -iE "(error|warning)" build.log | \
  grep -v "obsolete\|compile time\|HTML_HEADER" | \
  grep -i "PLUGINNAME"
```

**Zero tolerance:** ANY plugin-specific errors or warnings must be fixed.

**Common build errors:**
- Missing anchor IDs (broken `\ref`)
- Malformed LaTeX equations
- Unclosed HTML tags
- Invalid cross-references

---

## Common Failure Modes and How to Avoid Them

### Failure Mode 1: "I'll just copy the theory sections manually"

**Why it fails:** You WILL miss sections, skip equations, drop table rows, forget footnotes.

**How to avoid:** Start with `cp native.dox pyhelios.md` - copy the ENTIRE file first.

### Failure Mode 2: "The API looks similar, I'll adapt it"

**Why it fails:** Python API ≠ C++ API. Material-based ≠ UUID-based. Method names differ.

**How to avoid:** Grep the actual Python source for EVERY method before documenting it.

### Failure Mode 3: "Equations are annoying, I'll simplify them"

**Why it fails:** Breaking LaTeX syntax breaks equation rendering. Users need exact equations for implementation.

**How to avoid:** Copy equations EXACTLY, character-for-character, including `\f$`, `\f[`, subscripts, superscripts.

### Failure Mode 4: "Backticks are fine for references"

**Why it fails:** Plain backticks don't create hyperlinks. Users can't navigate documentation.

**How to avoid:** Use `\ref` for ALL cross-references to classes, methods, plugins, and sections.

### Failure Mode 5: "I'll convert everything at once"

**Why it fails:** Large complex documents introduce errors. You lose track of what's theory vs API.

**How to avoid:** Work section-by-section, get approval after EACH section.

### Failure Mode 6: "Close enough is fine"

**Why it fails:** "Close enough" means wrong equations, missing species data, broken references.

**How to avoid:** 100% accuracy requirement. If native doc has it, PyHelios doc must have it.

---

## Detailed Checklist for Each Section Type

### For Theory Sections (BWB, BBL, MOPT, BMF, etc.)

- [ ] Section header converted: `\section TheoryID` → `## Title {#TheoryID}`
- [ ] ALL equation blocks preserved with `\f[...\f]` syntax
- [ ] ALL inline equations preserved with `\f$...\f$` syntax
- [ ] ALL external paper links preserved (URLs)
- [ ] ALL species parameter tables copied exactly (every row, every value)
- [ ] ALL footnotes and disclaimers preserved
- [ ] NO paraphrasing or simplification of theoretical content
- [ ] Typos from native doc preserved (don't "fix" them - maintain exact consistency)

### For Primitive Data Tables

- [ ] Table structure preserved exactly (all columns, all rows)
- [ ] All symbols in `\f$...\f$` format preserved
- [ ] All units with superscripts/subscripts preserved
- [ ] All default values preserved exactly
- [ ] All `\ref PluginName` cross-references preserved
- [ ] HTML formatting (`\htmlonly`, `<span>`, etc.) preserved
- [ ] Footnotes with `**` or `\*\*` preserved

### For Code Examples

- [ ] Verified method exists in PyHelios source with grep
- [ ] Verified method signature matches (parameter names, types, order)
- [ ] Verified all imports are valid (test with `python -c "from ..."`)
- [ ] Context managers used correctly (`with Context() as context:`)
- [ ] Type imports correct (`from pyhelios.types import vec3, vec2`)
- [ ] NO C++-specific API (materials, pointers, etc.) unless verified in Python
- [ ] Comments preserved from native examples
- [ ] Example purpose/intent preserved

### For Cross-References

- [ ] All `\ref ClassName` preserved (links to API docs)
- [ ] All `\ref ClassName::method` preserved (links to method docs)
- [ ] All `\ref SectionID` preserved (internal navigation)
- [ ] NO plain backticks used for cross-references
- [ ] Verified each referenced class/method exists in PyHelios

---

## Section-by-Section Workflow Template

Use this exact workflow for EVERY plugin documentation sync:

### Phase 1: Preparation

```bash
# 1. Backup existing PyHelios doc
cp docs/plugin_PLUGINNAME.md docs/plugin_PLUGINNAME.md.backup

# 2. Copy native doc to REPLACE PyHelios doc (DO NOT SKIP THIS)
cp helios-core/plugins/PLUGINNAME/doc/PLUGINNAME.dox docs/plugin_PLUGINNAME.md

# 3. Copy any figures
cp helios-core/plugins/PLUGINNAME/doc/images/* docs/images/ 2>/dev/null || true

# 4. Check Doxygen config consistency
diff <(grep USE_MATHJAX docs/Doxyfile.python) <(grep USE_MATHJAX helios-core/doc/Doxyfile)
```

### Phase 2: Section-by-Section Conversion

**For EACH section:**

1. **Read** the section in native doc (note line numbers)
2. **Identify** what needs to change (only C++ code examples)
3. **Convert** Doxygen syntax to markdown syntax
4. **Preserve** ALL content, equations, tables, references
5. **Verify** the converted section
6. **Get approval** before moving to next section

**Section Order:**
1. Header and Overview
2. Primitive Data Tables
3. Introduction/Background
4. Theory Sections (one per model)
5. Usage Examples
6. PyHelios-Specific Sections

### Phase 3: API Accuracy Verification

**For EVERY code example:**

```python
# 1. Extract imports and verify
python -c "from pyhelios import Context, PluginClass"

# 2. Grep for method existence
grep -rn "def methodName" pyhelios/PluginClass.py

# 3. Read method signature
# Verify: parameter names, types, defaults match your documentation

# 4. Check for common API mismatches
grep -rn "def setModelCoefficients" pyhelios/  # Might not exist
grep -rn "def setBMFCoefficients" pyhelios/    # Model-specific methods
```

**If method doesn't exist in Python:**
- Use the correct Python equivalent
- Add note if functionality is C++-only
- Don't fake it or assume it exists

### Phase 4: Build and Test

```bash
# Build documentation
cd docs
doxygen Doxyfile.python 2>&1 | tee build.log

# Check for errors (filtering known non-issues)
grep -iE "(error|warning)" build.log | \
  grep -v "obsolete\|compile time" | \
  grep -i "PLUGINNAME"

# If ANY errors exist: STOP and fix them
```

**Zero tolerance for errors:** Fix every error before proceeding.

### Phase 5: Cross-Reference Audit

```bash
# Extract all \ref references
grep -o '\\ref [A-Za-z_:]*' docs/plugin_PLUGINNAME.md | sort -u > refs.txt

# For each reference, verify it exists:
# - Plugin classes: check if plugin exists
# - Methods: grep for method definition
# - Sections: check anchor ID exists in doc
# - Coefficient structures: verify Python class exists
```

**If reference is broken:**
- Fix the reference if target name changed
- Update to Python equivalent if C++ specific
- Add the missing anchor if section ID is wrong

### Phase 6: Final Verification

**Run code-reviewer agent with this specific prompt:**

```
Review docs/plugin_PLUGINNAME.md for:
1. 100% accuracy of all code snippets (verify against PyHelios source)
2. All cross-references use proper \ref syntax and link to valid targets
3. All equations preserved in \f$ and \f[ format
4. Compare against native doc - verify NO sections omitted
5. Check git status - confirm files properly tracked
```

**Act on ALL findings before considering task complete.**

---

## Critical "Don't Do" List

### ❌ DON'T Try to Be Clever

**Wrong approach:**
```
"I'll read both docs and create an optimal combined version"
```

**Right approach:**
```
"I'll copy native doc exactly, then systematically convert format, then adapt API examples"
```

### ❌ DON'T Assume API Equivalence

**Wrong:**
```python
# "C++ has setModelCoefficients(), so Python must too"
stomatal.setModelCoefficients(coeffs)
```

**Right:**
```bash
# Verify first
grep -rn "def setModelCoefficients" pyhelios/
# Not found? Use correct Python method:
stomatal.setBMFCoefficients(coeffs)
```

### ❌ DON'T Paraphrase Theory

**Wrong:**
```
"The Ball-Berry model uses photosynthesis and humidity to calculate conductance"
```

**Right:**
```
[Copy exact text from native doc including citations]
"The Ball, Woodrow, and Berry (1987) model is based on the empirical
observation that stomatal conductance various roughly linearly with..."
```

### ❌ DON'T Skip Verification Steps

**Wrong workflow:**
```
1. Convert doc
2. Build docs
3. Done!
```

**Right workflow:**
```
1. Convert doc section-by-section with approval
2. Build docs and fix errors
3. Code review with detailed checklist
4. Fix all issues found
5. Rebuild to verify fixes
6. Add to git
7. Done!
```

### ❌ DON'T Use Backticks for Cross-References

**Wrong:**
```markdown
See the `RadiationModel` plugin for more info.
Call `setBMFCoefficients()` to set coefficients.
```

**Right:**
```markdown
See the \ref RadiationModel plugin for more info.
Call \ref StomatalConductanceModel::setBMFCoefficients() to set coefficients.
```

### ❌ DON'T Modify Equations "to make them clearer"

**Wrong:**
```
Converting \f$C_s\f$ to C_s because "it's simpler"
```

**Right:**
```
Keep \f$C_s\f$ EXACTLY as-is for proper MathJax rendering
```

---

## Tools and Commands Reference

### Verification Commands

```bash
# Check equation syntax
grep '\\f\[' docs/plugin_PLUGINNAME.md | wc -l  # Count display equations
grep '\\f\$' docs/plugin_PLUGINNAME.md | wc -l  # Count inline equations

# Check cross-references
grep '\\ref' docs/plugin_PLUGINNAME.md | wc -l

# Compare section count with native
grep '\\section' helios-core/plugins/PLUGINNAME/doc/*.dox | wc -l
grep '^##' docs/plugin_PLUGINNAME.md | wc -l

# Find all figures referenced
grep -E '\!\[.*\]\(.*\)|<img.*src=' docs/plugin_PLUGINNAME.md

# Check if all code blocks are valid Python
# Extract all ```python blocks and syntax check them
```

### API Verification Commands

```bash
# Find all classes in a plugin
grep "^class " pyhelios/PluginName.py

# Find all public methods
grep "    def [^_]" pyhelios/PluginName.py

# Check if import works
python -c "from pyhelios import ClassName; print(dir(ClassName))"

# Verify method signature
python -c "from pyhelios import ClassName; import inspect; print(inspect.signature(ClassName.methodName))"
```

### Documentation Build Commands

```bash
# Full build
cd docs && doxygen Doxyfile.python

# Quick error check
doxygen Doxyfile.python 2>&1 | grep -iE "error.*plugin"

# View generated docs
open docs/generated/html/plugin_PLUGINNAME.html  # macOS
# or xdg-open on Linux, start on Windows
```

---

## Quality Metrics for Success

A successfully synchronized documentation has:

✅ **100% Theoretical Accuracy**
- Every equation from native doc present
- Every table row from native doc present
- Every scientific reference from native doc present
- Zero paraphrasing of theory content

✅ **100% API Accuracy**
- Every code example runs without errors
- Every import statement works
- Every method call uses correct signature
- Zero references to non-existent methods

✅ **100% Cross-Reference Accuracy**
- All `\ref` links point to valid targets
- All plugin references correct
- All method references correct
- All internal anchors work

✅ **Build Quality**
- Zero errors in Doxygen build
- Zero warnings about plugin content
- MathJax equations render correctly
- All cross-reference links work in generated HTML

✅ **Git Hygiene**
- Documentation file added to git
- Doxyfile.python changes added to git
- Figures (if any) added to git
- Backup files NOT added to git

---

## Red Flags That You're Doing It Wrong

🚩 **You're skipping sections** - "That section isn't important for Python"
→ **Fix:** ALL theory sections are important. Copy everything.

🚩 **You're simplifying equations** - "I'll make this equation more readable"
→ **Fix:** Copy equations character-for-character.

🚩 **You're using backticks** - "Just use `ClassName` it's easier"
→ **Fix:** Use `\ref ClassName` for proper hyperlinking.

🚩 **You're writing code from memory** - "I know the Python API"
→ **Fix:** Grep the source code to verify EVERY method.

🚩 **You're making it "better"** - "I'll reorganize for clarity"
→ **Fix:** Match native doc structure exactly.

🚩 **You're batch converting** - "I'll convert the whole doc at once"
→ **Fix:** Work section-by-section with approval.

🚩 **You're seeing build warnings** - "Just warnings, not errors"
→ **Fix:** Fix ALL warnings related to your plugin.

🚩 **Code reviewer found issues** - "Minor issues, probably fine"
→ **Fix:** Fix EVERY issue before declaring complete.

---

## Post-Sync Maintenance

### When Native Docs Are Updated

```bash
# 1. Check what changed in native
cd helios-core/plugins/PLUGINNAME/doc
git log -p PLUGINNAME.dox

# 2. Apply same changes to PyHelios doc
# Follow same section-by-section workflow
# Update theory/equations to match
# Keep Python API examples as-is (unless API changed)

# 3. Rebuild and verify
cd docs && doxygen Doxyfile.python
```

### Keeping Track of API Divergence

When Python API differs from C++ API, document it:

```markdown
**Note:** The C++ API includes material-based coefficient setting
(see native documentation). PyHelios currently uses UUID-based approach:

\```python
# Python API (UUID-based)
stomatal.setBMFCoefficients(coeffs, uuids=[uuid1, uuid2])
\```

See [C++ documentation](link) for material-based approach.
```

---

## Success Story: Stomatal Conductance Sync (2025-12-03)

**What worked:**
- Started with exact copy of native doc
- Worked section-by-section with user approval
- Fixed Doxyfile.python MathJax config FIRST
- Used code-reviewer agent to catch API errors
- Fixed all issues before declaring complete

**What didn't work initially:**
- Tried to create "combined" doc from scratch (missed sections)
- Didn't verify API methods existed (used wrong method names)
- Used backticks instead of `\ref` (broke hyperlinking)
- Tried to batch-convert (introduced errors)

**Time saved by following proper workflow:** ~2 hours of debugging and rework

**Lesson:** Following the systematic workflow is FASTER than trying shortcuts.

---

## Final Wisdom

**The Golden Rule:**
> When synchronizing documentation, your job is NOT to improve it,
> NOT to simplify it, and NOT to make it "better for Python users."
>
> Your job is to ensure theoretical content is IDENTICAL to native docs,
> while API examples use correct PyHelios syntax.

**The Test:**
> A physicist should be able to implement the model from your equations.
> A programmer should be able to run your code examples without errors.
> Both should get identical results whether using C++ or Python.

**When in doubt:**
> Copy more rather than less.
> Verify rather than assume.
> Ask user rather than guess.

---

## Appendix: Template for Different Plugin Types

### Computational Plugins (No Dependencies)

Examples: StomatalConductance, BoundaryLayerConductance

**Key characteristics:**
- No GPU requirements
- No external dependencies
- Pure math/physics calculations
- Heavy on theory sections

**Sync focus:**
- Theory sections are the bulk of the doc
- Multiple models with equations
- Species parameter tables
- Minimal API surface

### GPU Plugins (OptiX/CUDA)

Examples: Radiation, AerialLiDAR

**Key characteristics:**
- Require OptiX/CUDA
- May need shader files
- Platform-specific builds

**Sync focus:**
- System requirements critical
- Shader/asset management
- GPU availability checking
- Performance notes important

### Visualization Plugins

Examples: Visualizer

**Key characteristics:**
- OpenGL dependencies
- Interactive controls
- Asset files (fonts, shaders, textures)

**Sync focus:**
- Asset copying in build system
- Control documentation
- Platform-specific rendering notes
- Performance/compatibility

### Geometry Plugins

Examples: WeberPennTree, CanopyGenerator

**Key characteristics:**
- Procedural generation
- Many configurable parameters
- Species libraries

**Sync focus:**
- Parameter tables are critical
- Species libraries must match
- Example geometry images
- Parameter effect documentation

---

## Conclusion

Documentation synchronization is a **PRECISION TASK**, not a creative task.

**Success comes from:**
1. Following the workflow exactly
2. Verifying every step
3. Preserving 100% of theory content
4. Ensuring 100% API accuracy
5. Getting section-by-section approval

**Failure comes from:**
1. Taking shortcuts
2. Assuming instead of verifying
3. Paraphrasing theory content
4. Using non-existent API methods
5. Batch converting without review

When future agents follow this guide exactly, documentation sync becomes a methodical, verifiable process instead of an error-prone struggle.
