# Content Alignment Explanation

## What is Fuzzy Matching?

**Fuzzy matching** is a technique to find similar strings even when they don't match exactly. Instead of requiring an exact match, it calculates a similarity score (0-100%) between two strings.

### Examples:

1. **Exact match**: "Atomic structure" = "Atomic structure" → 100% match
2. **Case difference**: "Atomic structure" vs "atomic structure" → ~95% match
3. **Partial match**: "Particles in the atom and atomic radius" vs "Particles in the atom" → ~75% match
4. **Similar meaning**: "Isotopes" vs "Isotope" → ~90% match
5. **Different wording**: "Electrons, energy levels and atomic orbitals" vs "Electrons in atoms" → ~60% match

### How it works:

Python's `difflib.SequenceMatcher` compares two strings character by character and calculates similarity:
- "Atomic structure" vs "atomic structure" = 0.95 (95% similar)
- "Isotopes" vs "Isotope" = 0.90 (90% similar)
- "Particles in the atom" vs "Particles in atom" = 0.95 (95% similar)

## Content Placement Strategy

### Step-by-Step Process:

#### 1. **Topic Matching** (Chapter → Topic)

**Syllabus Topic 1**: "Atomic structure"
**Textbook Chapter 2**: "Atomic structure"

**Matching Process**:
- Normalize both: "atomic structure" vs "atomic structure"
- Calculate similarity: 100% match ✓
- **Result**: Chapter 2 content goes under Topic 1

**Syllabus Topic 2**: "Atoms, molecules and stoichiometry"  
**Textbook Chapter 1**: "Moles and equations"

**Matching Process**:
- Normalize: "atoms molecules stoichiometry" vs "moles equations"
- Check keywords: "moles" relates to "stoichiometry" (chemistry concept)
- Calculate similarity: ~65% match
- **Result**: Chapter 1 content goes under Topic 2 (best match)

#### 2. **Subtopic Matching** (Section → Subtopic)

Once we know Chapter 2 maps to Topic 1, we match sections to subtopics:

**Syllabus Subtopic 1.1**: "Particles in the atom and atomic radius"
**Textbook Sections in Chapter 2**:
- "Elements and atoms" → Check keywords: "atoms", "particles" → ~70% match
- "Inside the atom" → Check keywords: "atom", "particles" → ~75% match  
- "Numbers of nucleons" → Check keywords: "nucleons" (particles) → ~60% match

**Strategy**: Combine all three sections since they all relate to particles in atoms
**Result**: All three sections' content combined → Subtopic 1.1

**Syllabus Subtopic 1.2**: "Isotopes"
**Textbook Section**: "Isotopes"

**Matching Process**:
- Exact match: "Isotopes" = "Isotopes" → 100% match ✓
- **Result**: Section content → Subtopic 1.2

**Syllabus Subtopic 1.3**: "Electrons, energy levels and atomic orbitals"
**Textbook Sections**:
- "Simple electronic structure" → Keywords: "electronic", "electrons" → ~80% match
- "Evidence for electronic structure" → Keywords: "electronic" → ~70% match

**Strategy**: Combine sections about electronic structure
**Result**: Combined content → Subtopic 1.3

#### 3. **Content Aggregation**

When multiple textbook sections match one subtopic:

**Example**: Subtopic 1.1 gets content from:
- Section "Elements and atoms" (content: "...")
- Section "Inside the atom" (content: "...")
- Section "Numbers of nucleons" (content: "...")

**Combined Content**:
```
[Section 1 Content]
---
[Section 2 Content]
---
[Section 3 Content]
```

### Final Structure:

```json
{
  "topics": [
    {
      "topic_number": "1",
      "topic_name": "Atomic structure",
      "sub_topics": [
        {
          "sub_topic_number": "1.1",
          "sub_topic_name": "Particles in the atom and atomic radius",
          "content": "[Combined from: Elements and atoms, Inside the atom, Numbers of nucleons]",
          "learning_objectives": [...]  // From syllabus
        },
        {
          "sub_topic_number": "1.2",
          "sub_topic_name": "Isotopes",
          "content": "[From: Isotopes section]",
          "learning_objectives": [...]
        }
      ]
    }
  ]
}
```

## Matching Algorithm Details

### Normalization Steps:
1. Convert to lowercase
2. Remove punctuation (.,!? etc.)
3. Remove common words ("the", "and", "in", "of")
4. Handle variations (singular/plural, British/American spelling)

### Similarity Thresholds:
- **> 80%**: Strong match (use directly)
- **60-80%**: Good match (use with confidence)
- **40-60%**: Weak match (use as best available)
- **< 40%**: Poor match (try keyword matching instead)

### Keyword Matching Fallback:
If fuzzy matching fails, check if key terms appear:
- "Particles" → matches "particle", "atom", "nucleon"
- "Isotopes" → matches "isotope", "isotopic"
- "Energy levels" → matches "energy", "level", "orbital", "shell"

## Example: Complete Matching Flow

**Syllabus Topic 1**: "Atomic structure"
- Find best chapter match → Chapter 2: "Atomic structure" (100% match)
- Extract all sections from Chapter 2

**For each syllabus subtopic under Topic 1**:

1. **Subtopic 1.1**: "Particles in the atom and atomic radius"
   - Match sections: "Elements and atoms" (70%), "Inside the atom" (75%), "Numbers of nucleons" (60%)
   - **Action**: Combine all three sections' content
   - **Place**: Under subtopic 1.1

2. **Subtopic 1.2**: "Isotopes"
   - Match section: "Isotopes" (100%)
   - **Action**: Use this section's content directly
   - **Place**: Under subtopic 1.2

3. **Subtopic 1.3**: "Electrons, energy levels and atomic orbitals"
   - Match sections: "Simple electronic structure" (80%), "Evidence for electronic structure" (70%)
   - **Action**: Combine these sections
   - **Place**: Under subtopic 1.3

4. **Subtopic 1.4**: "Ionisation energy"
   - Match section: "Evidence for electronic structure" (contains "ionisation energy" keywords)
   - **Action**: Extract relevant portion or use full section
   - **Place**: Under subtopic 1.4

## Handling Edge Cases

### Multiple Sections → One Subtopic:
Combine all matching sections with separator "---"

### One Section → Multiple Subtopics:
Split section content based on keywords or use full content for best match

### No Match Found:
- Use best available match (even if low similarity)
- Log warning in alignment report
- Include content in "unmatched" section for review

### Partial Matches:
- If section title partially matches, check content keywords
- If content contains key terms from subtopic, include it

