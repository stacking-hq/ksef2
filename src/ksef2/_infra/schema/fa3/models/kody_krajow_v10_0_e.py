from __future__ import annotations

from enum import Enum

__NAMESPACE__ = (
    "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/"
)


class TkodKraju(Enum):
    """
    Słownik kodów krajów.

    Attributes:
        AF: AFGANISTAN
        AX: ALAND ISLANDS
        AL: ALBANIA
        DZ: ALGIERIA
        AD: ANDORA
        AO: ANGOLA
        AI: ANGUILLA
        AQ: ANTARKTYDA
        AG: ANTIGUA I BARBUDA
        AN: ANTYLE HOLENDERSKIE
        SA: ARABIA SAUDYJSKA
        AR: ARGENTYNA
        AM: ARMENIA
        AW: ARUBA
        AU: AUSTRALIA
        AT: AUSTRIA
        AZ: AZERBEJDŻAN
        BS: BAHAMY
        BH: BAHRAJN
        BD: BANGLADESZ
        BB: BARBADOS
        BE: BELGIA
        BZ: BELIZE
        BJ: BENIN
        BM: BERMUDY
        BT: BHUTAN
        BY: BIAŁORUŚ
        BO: BOLIWIA
        BQ: BONAIRE, SINT EUSTATIUS I SABA
        BA: BOŚNIA I HERCEGOWINA
        BW: BOTSWANA
        BR: BRAZYLIA
        BN: BRUNEI DARUSSALAM
        IO: BRYTYJSKIE TERYTORIUM OCEANU INDYJSKIEGO
        BG: BUŁGARIA
        BF: BURKINA FASO
        BI: BURUNDI
        XC: CEUTA
        CL: CHILE
        CN: CHINY
        HR: CHORWACJA
        CW: CURAÇAO
        CY: CYPR
        TD: CZAD
        ME: CZARNOGÓRA
        DK: DANIA
        DM: DOMINIKA
        DO: DOMINIKANA
        DJ: DŻIBUTI
        EG: EGIPT
        EC: EKWADOR
        ER: ERYTREA
        EE: ESTONIA
        ET: ETIOPIA
        FK: FALKLANDY
        FJ: FIDŻI REPUBLIKA
        PH: FILIPINY
        FI: FINLANDIA
        FR: FRANCJA
        TF: FRANCUSKIE TERYTORIUM POŁUDNIOWE
        GA: GABON
        GM: GAMBIA
        GH: GHANA
        GI: GIBRALTAR
        GR: GRECJA
        GD: GRENADA
        GL: GRENLANDIA
        GE: GRUZJA
        GU: GUAM
        GG: GUERNSEY
        GY: GUJANA
        GF: GUJANA FRANCUSKA
        GP: GWADELUPA
        GT: GWATEMALA
        GN: GWINEA
        GQ: GWINEA RÓWNIKOWA
        GW: GWINEA-BISSAU
        HT: HAITI
        ES: HISZPANIA
        HN: HONDURAS
        HK: HONGKONG
        IN: INDIE
        ID: INDONEZJA
        IQ: IRAK
        IR: IRAN
        IE: IRLANDIA
        IS: ISLANDIA
        IL: IZRAEL
        JM: JAMAJKA
        JP: JAPONIA
        YE: JEMEN
        JE: JERSEY
        JO: JORDANIA
        KY: KAJMANY
        KH: KAMBODŻA
        CM: KAMERUN
        CA: KANADA
        QA: KATAR
        KZ: KAZACHSTAN
        KE: KENIA
        KG: KIRGISTAN
        KI: KIRIBATI
        CO: KOLUMBIA
        KM: KOMORY
        CG: KONGO
        CD: KONGO, REPUBLIKA DEMOKRATYCZNA
        KP: KOREAŃSKA REPUBLIKA LUDOWO-DEMOKRATYCZNA
        XK: KOSOWO
        CR: KOSTARYKA
        CU: KUBA
        KW: KUWEJT
        LA: LAOS
        LS: LESOTHO
        LB: LIBAN
        LR: LIBERIA
        LY: LIBIA
        LI: LIECHTENSTEIN
        LT: LITWA
        LV: ŁOTWA
        LU: LUKSEMBURG
        MK: MACEDONIA
        MG: MADAGASKAR
        YT: MAJOTTA
        MO: MAKAU
        MW: MALAWI
        MV: MALEDIWY
        MY: MALEZJA
        ML: MALI
        MT: MALTA
        MP: MARIANY PÓŁNOCNE
        MA: MAROKO
        MQ: MARTYNIKA
        MR: MAURETANIA
        MU: MAURITIUS
        MX: MEKSYK
        XL: MELILLA
        FM: MIKRONEZJA
        UM: MINOR
        MD: MOŁDOWA
        MC: MONAKO
        MN: MONGOLIA
        MS: MONTSERRAT
        MZ: MOZAMBIK
        MM: MYANMAR (BURMA)
        NA: NAMIBIA
        NR: NAURU
        NP: NEPAL
        NL: NIDERLANDY (HOLANDIA)
        DE: NIEMCY
        NE: NIGER
        NG: NIGERIA
        NI: NIKARAGUA
        NU: NIUE
        NF: NORFOLK
        NO: NORWEGIA
        NC: NOWA KALEDONIA
        NZ: NOWA ZELANDIA
        PS: OKUPOWANE TERYTORIUM PALESTYNY
        OM: OMAN
        PK: PAKISTAN
        PW: PALAU
        PA: PANAMA
        PG: PAPUA NOWA GWINEA
        PY: PARAGWAJ
        PE: PERU
        PN: PITCAIRN
        PF: POLINEZJA FRANCUSKA
        PL: POLSKA
        GS: POŁUDNIOWA GEORGIA I POŁUD.WYSPY SANDWICH
        PT: PORTUGALIA
        PR: PORTORYKO
        CF: REP.ŚRODKOWOAFRYKAŃSKA
        CZ: REPUBLIKA CZESKA
        KR: REPUBLIKA KOREI
        ZA: REPUBLIKA POŁUDNIOWEJ AFRYKI
        RE: REUNION
        RU: ROSJA
        RO: RUMUNIA
        RW: RWANDA
        EH: SAHARA ZACHODNIA
        BL: SAINT BARTHELEMY
        KN: SAINT KITTS I NEVIS
        LC: SAINT LUCIA
        MF: SAINT MARTIN
        VC: SAINT VINCENT I GRENADYNY
        SV: SALWADOR
        WS: SAMOA
        AS: SAMOA AMERYKAŃSKIE
        SM: SAN MARINO
        SN: SENEGAL
        RS: SERBIA
        SC: SESZELE
        SL: SIERRA LEONE
        SG: SINGAPUR
        SK: SŁOWACJA
        SI: SŁOWENIA
        SO: SOMALIA
        LK: SRI LANKA
        PM: SAINT PIERRE I MIQUELON
        US: STANY ZJEDNOCZONE AMERYKI
        SZ: SUAZI
        SD: SUDAN
        SS: SUDAN POŁUDNIOWY
        SR: SURINAM
        SJ: SVALBARD I JAN MAYEN
        SH: ŚWIĘTA HELENA
        SY: SYRIA
        CH: SZWAJCARIA
        SE: SZWECJA
        TJ: TADŻYKISTAN
        TH: TAJLANDIA
        TW: TAJWAN
        TZ: TANZANIA
        TG: TOGO
        TK: TOKELAU
        TO: TONGA
        TT: TRYNIDAD I TOBAGO
        TN: TUNEZJA
        TR: TURCJA
        TM: TURKMENISTAN
        TV: TUVALU
        UG: UGANDA
        UA: UKRAINA
        UY: URUGWAJ
        UZ: UZBEKISTAN
        VU: VANUATU
        WF: WALLIS I FUTUNA
        VA: WATYKAN
        HU: WĘGRY
        VE: WENEZUELA
        GB: WIELKA BRYTANIA
        VN: WIETNAM
        IT: WŁOCHY
        TL: WSCHODNI TIMOR
        CI: WYBRZEŻE KOŚCI SŁONIOWEJ
        BV: WYSPA BOUVETA
        CX: WYSPA BOŻEGO NARODZENIA
        IM: WYSPA MAN
        SX: WYSPA SINT MAARTEN (CZĘŚĆ HOLENDERSKA WYSPY)
        CK: WYSPY COOKA
        VI: WYSPY DZIEWICZE-USA
        VG: WYSPY DZIEWICZE-W.B.
        HM: WYSPY HEARD I MCDONALD
        CC: WYSPY KOKOSOWE (KEELINGA)
        MH: WYSPY MARSHALLA
        FO: WYSPY OWCZE
        SB: WYSPY SALOMONA
        ST: WYSPY ŚWIĘTEGO TOMASZA I KSIĄŻĘCA
        TC: WYSPY TURKS I CAICOS
        ZM: ZAMBIA
        CV: ZIELONY PRZYLĄDEK
        ZW: ZIMBABWE
        AE: ZJEDNOCZONE EMIRATY ARABSKIE
        XI: ZJEDNOCZONE KRÓLESTWO (IRLANDIA PÓŁNOCNA)
    """

    AF = "AF"
    AX = "AX"
    AL = "AL"
    DZ = "DZ"
    AD = "AD"
    AO = "AO"
    AI = "AI"
    AQ = "AQ"
    AG = "AG"
    AN = "AN"
    SA = "SA"
    AR = "AR"
    AM = "AM"
    AW = "AW"
    AU = "AU"
    AT = "AT"
    AZ = "AZ"
    BS = "BS"
    BH = "BH"
    BD = "BD"
    BB = "BB"
    BE = "BE"
    BZ = "BZ"
    BJ = "BJ"
    BM = "BM"
    BT = "BT"
    BY = "BY"
    BO = "BO"
    BQ = "BQ"
    BA = "BA"
    BW = "BW"
    BR = "BR"
    BN = "BN"
    IO = "IO"
    BG = "BG"
    BF = "BF"
    BI = "BI"
    XC = "XC"
    CL = "CL"
    CN = "CN"
    HR = "HR"
    CW = "CW"
    CY = "CY"
    TD = "TD"
    ME = "ME"
    DK = "DK"
    DM = "DM"
    DO = "DO"
    DJ = "DJ"
    EG = "EG"
    EC = "EC"
    ER = "ER"
    EE = "EE"
    ET = "ET"
    FK = "FK"
    FJ = "FJ"
    PH = "PH"
    FI = "FI"
    FR = "FR"
    TF = "TF"
    GA = "GA"
    GM = "GM"
    GH = "GH"
    GI = "GI"
    GR = "GR"
    GD = "GD"
    GL = "GL"
    GE = "GE"
    GU = "GU"
    GG = "GG"
    GY = "GY"
    GF = "GF"
    GP = "GP"
    GT = "GT"
    GN = "GN"
    GQ = "GQ"
    GW = "GW"
    HT = "HT"
    ES = "ES"
    HN = "HN"
    HK = "HK"
    IN = "IN"
    ID = "ID"
    IQ = "IQ"
    IR = "IR"
    IE = "IE"
    IS = "IS"
    IL = "IL"
    JM = "JM"
    JP = "JP"
    YE = "YE"
    JE = "JE"
    JO = "JO"
    KY = "KY"
    KH = "KH"
    CM = "CM"
    CA = "CA"
    QA = "QA"
    KZ = "KZ"
    KE = "KE"
    KG = "KG"
    KI = "KI"
    CO = "CO"
    KM = "KM"
    CG = "CG"
    CD = "CD"
    KP = "KP"
    XK = "XK"
    CR = "CR"
    CU = "CU"
    KW = "KW"
    LA = "LA"
    LS = "LS"
    LB = "LB"
    LR = "LR"
    LY = "LY"
    LI = "LI"
    LT = "LT"
    LV = "LV"
    LU = "LU"
    MK = "MK"
    MG = "MG"
    YT = "YT"
    MO = "MO"
    MW = "MW"
    MV = "MV"
    MY = "MY"
    ML = "ML"
    MT = "MT"
    MP = "MP"
    MA = "MA"
    MQ = "MQ"
    MR = "MR"
    MU = "MU"
    MX = "MX"
    XL = "XL"
    FM = "FM"
    UM = "UM"
    MD = "MD"
    MC = "MC"
    MN = "MN"
    MS = "MS"
    MZ = "MZ"
    MM = "MM"
    NA = "NA"
    NR = "NR"
    NP = "NP"
    NL = "NL"
    DE = "DE"
    NE = "NE"
    NG = "NG"
    NI = "NI"
    NU = "NU"
    NF = "NF"
    NO = "NO"
    NC = "NC"
    NZ = "NZ"
    PS = "PS"
    OM = "OM"
    PK = "PK"
    PW = "PW"
    PA = "PA"
    PG = "PG"
    PY = "PY"
    PE = "PE"
    PN = "PN"
    PF = "PF"
    PL = "PL"
    GS = "GS"
    PT = "PT"
    PR = "PR"
    CF = "CF"
    CZ = "CZ"
    KR = "KR"
    ZA = "ZA"
    RE = "RE"
    RU = "RU"
    RO = "RO"
    RW = "RW"
    EH = "EH"
    BL = "BL"
    KN = "KN"
    LC = "LC"
    MF = "MF"
    VC = "VC"
    SV = "SV"
    WS = "WS"
    AS = "AS"
    SM = "SM"
    SN = "SN"
    RS = "RS"
    SC = "SC"
    SL = "SL"
    SG = "SG"
    SK = "SK"
    SI = "SI"
    SO = "SO"
    LK = "LK"
    PM = "PM"
    US = "US"
    SZ = "SZ"
    SD = "SD"
    SS = "SS"
    SR = "SR"
    SJ = "SJ"
    SH = "SH"
    SY = "SY"
    CH = "CH"
    SE = "SE"
    TJ = "TJ"
    TH = "TH"
    TW = "TW"
    TZ = "TZ"
    TG = "TG"
    TK = "TK"
    TO = "TO"
    TT = "TT"
    TN = "TN"
    TR = "TR"
    TM = "TM"
    TV = "TV"
    UG = "UG"
    UA = "UA"
    UY = "UY"
    UZ = "UZ"
    VU = "VU"
    WF = "WF"
    VA = "VA"
    HU = "HU"
    VE = "VE"
    GB = "GB"
    VN = "VN"
    IT = "IT"
    TL = "TL"
    CI = "CI"
    BV = "BV"
    CX = "CX"
    IM = "IM"
    SX = "SX"
    CK = "CK"
    VI = "VI"
    VG = "VG"
    HM = "HM"
    CC = "CC"
    MH = "MH"
    FO = "FO"
    SB = "SB"
    ST = "ST"
    TC = "TC"
    ZM = "ZM"
    CV = "CV"
    ZW = "ZW"
    AE = "AE"
    XI = "XI"
