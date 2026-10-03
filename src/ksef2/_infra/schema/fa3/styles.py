DEFAULT_CSS_OVERRIDES = """
@page {
    size: A4 landscape;
    margin: 0.0cm;
}

table.white-space {
    table-layout: fixed !important;
    width: 100% !important;
    border-collapse: collapse;
}

table.white-space td {
    font-size: 6.5pt !important;
    padding: 2px 1px !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
    word-break: break-all !important;
    line-height: 1.1;
}

table.white-space td:nth-child(1) { width: 3%; }  /* Lp */
table.white-space td:nth-child(2) { width: 5%; } /* UUID  */
table.white-space td:nth-child(3) { width: 13%; } /* Name */
table.white-space td:nth-child(4) { width: 4%; }  /* Indeks */
table.white-space td:nth-child(5) { width: 4%; }  /* Jednostka */
table.white-space td:nth-child(6) { width: 4%; }  /* Ilość */
table.white-space td:nth-child(7) { width: 6%; }  /* Cena */
table.white-space td:nth-child(8) { width: 4%; }  /* Opusty */
table.white-space td:nth-child(9) { width: 6%; }  /* Wartość */
table.white-space td:nth-child(10) { width: 4%; } /* Kwota VAT */
table.white-space td:nth-child(11) { width: 4%; } /* Stawka VAT */
table.white-space td:nth-child(12) { width: 4%; } /* Stawka od... */
table.white-space td:nth-child(13) { width: 6%; } /* Data dok... */
table.white-space td:nth-child(14) { width: 4%; } /* Klasyfikacja */
table.white-space td:nth-child(15) { width: 4%; } /* Kwota akcyz */
table.white-space td:nth-child(16) { width: 4%; } /* Oznaczenie */
table.white-space td:nth-child(17) { width: 4%; } /* Kurs */
table.white-space td:nth-child(18) { width: 4%; } /* Znacznik 15 */
table.white-space td:nth-child(19) { width: 4%; } /* Znacznik korekta */

table.white-space tr {
    page-break-inside: avoid !important;
}
    """
