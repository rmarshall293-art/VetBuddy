"""MoneyLife Military: the Financial OS core (ADR 0008; v8 module #9).

Rebuilt from "VetBuddy Financial OS — Complete Specification" v4.0 and its
browser prototype. One deterministic engine in two languages: this package
and ``web/moneylife.js``, held identical by shared golden cases
(``tests/test_moneylife.py``), so the guest app can run it with nothing sent
anywhere.

Rules carried from the specification (§3, §10, §11, critical controls):
  - money is integer cents; interest uses integer fixed-point, never floats
  - unknown is never zero: a missing amount is left out and named
  - invalid values are refused (negative, non-integer, out of range)
  - an illustrative VA amount, and proposed law such as the Major Richard
    Star Act, are never counted as confirmed income
  - retired pay and VA compensation are never simply added together
  - VA compensation isn't counted alongside active-duty pay
  - DoD and VA disability percentages are separate inputs
  - every result carries its ruleset, sources, effective date, assumptions,
    exclusions, data status, confidence, warnings and an audit id

Pure library: no I/O beyond reading its rules, no persistence, no network,
no model. Saved scenarios come after sign-in (G17).
"""

ENGINE_NAME = "vetbuddy.moneylife.core"
ENGINE_VERSION = "1.0.0"
