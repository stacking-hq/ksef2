Here is a comprehensive, highly structured prompt designed specifically to be copied and pasted directly to a coding agent (like Aider, AutoGPT, or ChatGPT/Claude with codebase context).

It gives the agent exact architectural directives, tells it exactly how to parse the Polish documentation, and sets strict boundaries to prevent it from writing spaghetti code.

***

# SYSTEM PROMPT / TASK DIRECTIVE FOR CODING AGENT

## 🎯 MISSION OBJECTIVE
You are a senior backend architect. Your task is to refactor and expand a Python-based Model Context Protocol (MCP) toolset and Domain Layer for generating Polish KSeF (Krajowy System e-Faktur) FA(3) XML invoices.

Currently, the system uses a monolithic `FA3InvoiceBuilder`. You must refactor this into an **Intent-Driven (Polymorphic) Builder Pattern**. We must support specific invoice types: Standard (`VAT`), Correction (`KOR`), Advance (`ZAL`), Settlement (`ROZ`), and Margin (`MARŻA`).

You will read the official Polish Ministry of Finance "Broszura Informacyjna FA(3)" (Information Brochure) to determine the strict business rules for each builder.

## ⚠️ ARCHITECTURAL PROBLEM & SOLUTION
**The Problem:** An invoice line for a Correction has entirely different required fields than an invoice line for an Advance invoice. If we use a single `add_line()` method with 60+ optional arguments, the LLMs calling our MCP tools will hallucinate and mix parameters.
**The Solution:** We will create specific Builder classes for each invoice intent. Each builder will have strictly typed `__init__` and `add_line` methods that *only* accept fields legally allowed for that specific invoice type. The MCP Service layer will route calls to the correct builder based on the active session's `intent`.

## 📖 HOW TO READ THE "BROSZURA INFORMACYJNA" (SOURCE OF TRUTH)
You must analyze the *Broszura Informacyjna FA(3)* to implement the business logic. Pay strict attention to the **"Stan" (Status)** column in the brochure's tables:
*   **M (Obligatoryjne / Mandatory):** Must be enforced as required arguments in our Python functions.
*   **O (Opcjonalne / Optional):** Handled as `Optional[Type] = None`.
*   **W (Warunkowe / Conditional):** *This is critical.* If the brochure states a field is "W" and the condition is "Wymagalny w przypadku gdy pole RodzajFaktury = KOR" (Required when Invoice Type is KOR), you **must** make this a mandatory argument in the `CorrectionInvoiceBuilder`.

## 🛠️ REQUIRED IMPLEMENTATION TASKS

### TASK 1: Define the Domain Interfaces
Create a base abstract class `BaseFA3Builder` and an Enum `DraftIntent`.
```python
class DraftIntent(Enum):
    STANDARD = "VAT"
    CORRECTION = "KOR"
    ADVANCE = "ZAL"
    SETTLEMENT = "ROZ"
    MARGIN = "MARZA"
```

### TASK 2: Implement the Specific Strategy Builders
You must create the following classes inheriting from `BaseFA3Builder`. Read the brochure to implement their specific constraints:

**1. `StandardInvoiceBuilder` (RodzajFaktury: VAT)**
*   **Lines:** Requires standard `P_7` (name), `P_8B` (quantity), `P_9A` (net price), `P_12` (VAT rate).
*   **Logic:** Must automatically calculate `P_13_x`, `P_14_x` (VAT aggregates) and `P_15` (Total gross).

**2. `CorrectionInvoiceBuilder` (RodzajFaktury: KOR)**
*   **Constructor:** MUST strictly require `PrzyczynaKorekty` (Correction Reason) and `NrKsefFaKorygowanej` (Original KSeF ID). Do not allow instantiation without them.
*   **Lines:** The line method (e.g., `correct_line`) must require `NrWierszaFaKorygowanej` (Original Line Number). Lines will represent differences (in minus / in plus).

**3. `AdvanceInvoiceBuilder` (RodzajFaktury: ZAL)**
*   **Constructor:** Requires the gross advance amount received.
*   **Lines:** Advance invoices DO NOT use standard `FakturaWiersz`. You must map the line inputs to the `Zamowienie` (Order) node (fields `P_7Z`, `P_11NettoZ`).
*   **Logic:** VAT is calculated "w stu" (from gross to net).

**4. `SettlementInvoiceBuilder` (RodzajFaktury: ROZ)**
*   **Constructor:** MUST require a list of previous KSeF IDs (`NrKsefFaZaliczkowej`).
*   **Logic:** The final amount to pay (`P_15`) must automatically equal the total order value MINUS the amounts already paid in the provided advance invoices. Implement the `Odliczenia` node logic.

**5. `MarginInvoiceBuilder` (Faktura Marża)**
*   **Constructor:** Must require a margin procedure flag (sets `P_106E_3` nodes).
*   **Lines (CRITICAL):** Margin invoices are legally forbidden from displaying VAT rates on lines. The `add_line` method **MUST NOT** accept a `vat_rate` parameter. If one is passed, raise a `ValueError`. It must omit `P_12` and `P_14_x` nodes in the XML.

### TASK 3: Update the State / Session Manager
Update the `InvoiceBuilderHandle` (Pydantic model) to track the active intent.
```python
class InvoiceBuilderHandle(BaseModel):
    uuid: UUID
    intent: DraftIntent
    builder: BaseFA3Builder # Polymorphic interface
    # ... keep existing state tracking
```

### TASK 4: Update the Service Layer & MCP Tool Routing
Refactor `LocalInvoiceBuilderService`.
1.  **Initialization:** Replace `create_invoice_builder` with specific initialization methods (`init_standard_draft`, `init_correction_draft(reason, ksef_id)`, etc.). These tools will set the `DraftIntent` for the UUID.
2.  **Line Routing:** The `add_line` method in the service must inspect `handle.intent` and route the payload to the correct builder.

*Example Routing Logic to Implement:*

```python
if handle._intent == DraftIntent.CORRECTION:
    if "original_line_nr" not in payload:
        raise InvalidInputError("Corrections require original_line_nr")
    handle.builder.correct_line(...)
elif handle._intent == DraftIntent.MARGIN:
    if payload.get("vat_rate") is not None:
        raise InvalidInputError("Margin invoices cannot contain VAT rates in lines.")
    handle.builder.add_margin_line(...)
```

## 🛑 STRICT RULES AND CONSTRAINTS FOR THE AGENT
1.  **NO GOD METHODS:** Do not attempt to merge all logic into a single `add_line` function with 60 `**kwargs`. Use strict, explicit typing for each builder.
2.  **FAIL FAST:** If the input violates KSeF rules for that specific intent (e.g., missing a correction reason), raise a descriptive `ValueError` or `pydantic.ValidationError` *immediately*. Do not wait until the `.to_xml()` build step. The LLM needs immediate feedback to self-correct.
3.  **DELEGATE MATH:** The LLM client will NOT calculate VAT sums, gross totals, or deduction math. Your Builder classes must calculate `P_13_1`, `P_14_1`, and `P_15` internally upon building the final dataclass state.
4.  **XML IS THE FINAL STEP:** Keep the builders working with Domain Python Dataclasses/Pydantic models. Only the final `.to_xml()` call should serialize to the KSeF XML schema.

Begin your work by analyzing the *Broszura Informacyjna FA(3)* specifically for the tags required by `KOR`, `ZAL`, and `ROZ` invoice types, and proceed with Task 1.
