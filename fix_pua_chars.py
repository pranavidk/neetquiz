#!/usr/bin/env python3
"""
fix_pua_chars.py

Replaces Symbol-font Private Use Area (PUA) Unicode characters in
public/questions.json with their correct Unicode equivalents.

These garbled characters come from PDF extraction of mock test papers
where the PDF used embedded Symbol/Wingdings fonts mapped to the
U+E000–U+F8FF Private Use Area.
"""
import json
import os
import sys

# Symbol font PUA → correct Unicode mapping
# Built from contextual analysis of all 181 affected questions
PUA_MAP = {
    # Greek lowercase
    '\uf061': 'α',    # alpha
    '\uf062': 'β',    # beta
    '\uf063': 'χ',    # chi
    '\uf065': 'ε',    # epsilon
    '\uf066': 'φ',    # phi
    '\uf067': 'γ',    # gamma
    '\uf06c': 'λ',    # lambda
    '\uf06d': 'μ',    # mu
    '\uf070': 'π',    # pi
    '\uf071': 'θ',    # theta
    '\uf072': 'ρ',    # rho
    '\uf073': 'σ',    # sigma
    '\uf074': 'τ',    # tau
    '\uf075': 'υ',    # upsilon (often used as 'v' in physics)
    '\uf077': 'ω',    # omega

    # Greek uppercase
    '\uf044': 'Δ',    # Delta
    '\uf057': 'Ω',    # Omega

    # Math operators and symbols
    '\uf0b4': '×',    # multiplication sign
    '\uf0b5': '∝',    # proportional to
    '\uf0b9': '≠',    # not equal to
    '\uf0b0': '°',    # degree sign
    '\uf0b3': '≥',    # greater than or equal
    '\uf0bb': '≈',    # approximately equal
    '\uf0be': '→',    # right arrow (used in reactions)
    '\uf0d7': '·',    # dot product / middle dot
    '\uf0ce': '∈',    # element of / belongs to
    '\uf0d0': '∠',    # angle
    '\uf0de': '→',    # right arrow (mapping)
    '\uf0ad': '↔',    # left-right arrow (equilibrium)
    '\uf0ae': '→',    # right arrow
    '\uf0af': '→',    # right arrow
    '\uf0a5': '∞',    # infinity
    '\uf083': '⇌',    # equilibrium arrows
    '\uf0c5': '⊥',    # perpendicular
    '\uf0e5': 'Σ',    # summation (from context: sum = 0)
    '\uf0f2': '∫',    # integral sign

    # Bracket parts (Symbol font bracket pieces)
    '\uf0e6': '(',    # left paren top
    '\uf0e7': '(',    # left paren mid  
    '\uf0e8': '(',    # left paren bottom
    '\uf0f6': ')',    # right paren top
    '\uf0f7': ')',    # right paren mid
    '\uf0f8': ')',    # right paren bottom

    # Square bracket pieces
    '\uf0e9': '[',    # left bracket top
    '\uf0ea': '[',    # left bracket mid
    '\uf0eb': '[',    # left bracket bottom
    '\uf0f9': ']',    # right bracket top
    '\uf0fa': ']',    # right bracket mid
    '\uf0fb': ']',    # right bracket bottom

    # Curly brace pieces
    '\uf0ec': '{',    # left brace top
    '\uf0ed': '{',    # left brace mid
    '\uf0ee': '{',    # left brace bottom
    '\uf0fc': '}',    # right brace top
    '\uf0fd': '}',    # right brace mid
    '\uf0fe': '}',    # right brace bottom

    # Miscellaneous
    '\uf03c': '<',    # less than
    '\uf03e': '>',    # greater than
    '\uf020': ' ',    # space

    # E0xx range (custom font mappings)
    '\ue072': '→',    # right arrow (from context)
    '\ue06c': 'ℓ',    # script l
    '\ue088': '⊖',    # circled minus / standard state
    '\ue083': '°',    # degree
}


def fix_string(s):
    """Replace all PUA characters in a string using the mapping table."""
    if not s:
        return s
    result = []
    for c in s:
        if c in PUA_MAP:
            result.append(PUA_MAP[c])
        elif '\ue000' <= c <= '\uf8ff':
            # Unknown PUA char — replace with a placeholder
            result.append(f'[?U+{ord(c):04X}]')
        else:
            result.append(c)
    return ''.join(result)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    questions_path = os.path.join(script_dir, "public", "questions.json")

    if not os.path.exists(questions_path):
        sys.exit(f"Error: {questions_path} does not exist.")

    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    fixed_count = 0
    total_chars_fixed = 0

    for q in questions:
        changed = False

        # Fix text
        old_text = q.get("text", "")
        new_text = fix_string(old_text)
        if new_text != old_text:
            q["text"] = new_text
            changed = True
            total_chars_fixed += sum(1 for a, b in zip(old_text, new_text) if a != b)

        # Fix options
        old_opts = q.get("options", [])
        new_opts = [fix_string(opt) for opt in old_opts]
        if new_opts != old_opts:
            q["options"] = new_opts
            changed = True
            for old_o, new_o in zip(old_opts, new_opts):
                total_chars_fixed += sum(1 for a, b in zip(old_o, new_o) if a != b)

        # Fix solution
        old_sol = q.get("solution", "")
        new_sol = fix_string(old_sol)
        if new_sol != old_sol:
            q["solution"] = new_sol
            changed = True

        if changed:
            fixed_count += 1

    # Save
    with open(questions_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    print(f"\n── PUA CHARACTER FIX SUMMARY ──────────")
    print(f"Questions fixed    : {fixed_count}")
    print(f"Characters replaced: {total_chars_fixed}")
    print(f"Saved to           : {questions_path}")

    # Check for any remaining unknown PUA chars
    remaining = set()
    with open(questions_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for q in data:
        for field in ['text', 'solution'] + q.get('options', []):
            if isinstance(field, str):
                for c in field:
                    if '\ue000' <= c <= '\uf8ff':
                        remaining.add(f'U+{ord(c):04X}')
    if remaining:
        print(f"WARNING: {len(remaining)} unknown PUA chars remain: {remaining}")
    else:
        print(f"All PUA characters successfully replaced!")


if __name__ == "__main__":
    main()
