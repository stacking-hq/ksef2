<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema">
	<xsl:param name="nazwy-dla-kodow" select="true()"/>
	<xsl:param name="schema-krajow" select="'http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/KodyKrajow_v10-0E.xsd'"/>
	<xsl:param name="schema-urzedow" select="'http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/KodyUrzedowSkarbowych/KodyUrzedowSkarbowych_v8-0E.xsd'"/>
	<xsl:param name="schema-urzedowexwus" select="'http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2021/12/23/eD/KodyUrzedowSkarbowychExWUS/KodyUrzedowSkarbowychExWUS_v8-0E.xsd'"/>
	<xsl:param name="schema-naczelnikow-urzedow" select="'http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2017/02/06/eD/KodyNaczelnikowUrzedowSkarbowych/KodyNaczelnikowUrzedowSkarbowych_v4-0E.xsd'"/>
	<xsl:param name="schema-walut" select="'http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2021/12/23/eD/KodyWalut/KodyWalut_v1-0E.xsd'"/>
	<xsl:template match="/">
		<html>
			<head>
				<title>
					<xsl:call-template name="TytulDokumentu"/>
				</title>
				<xsl:call-template name="StyleWspolne"/>
				<xsl:call-template name="StyleDlaFormularza"/>
			</head>
			<body>
				<xsl:apply-templates/>
			</body>
		</html>
	</xsl:template>
	<xsl:template name="TytulDokumentu"/>
	<xsl:template name="StyleDlaFormularza"/>
	<xsl:template name="Podmiot">
		<xsl:param name="sekcja"/>
		<xsl:param name="pokazuj-adres" select="true()"/>
		<xsl:param name="wstaw-przed-ident"/>
		<xsl:param name="wstaw-za-ident"/>
		<xsl:param name="wstaw-przed-adres"/>
		<xsl:param name="wstaw-za-adres"/>
		<xsl:variable name="tytul-sekcji">
			<xsl:choose>
				<xsl:when test="@rola='Strona umowy'">DANE STRONY UMOWY</xsl:when>
				<xsl:when test="@rola='NierezydentŚwiadczącyUsługi'">DANE NIEREZYDENTA ŚWIADCZĄCEGO USŁUGI (WYKONUJĄCEGO PRACĘ)</xsl:when>
				<xsl:when test="@rola='SkładającyInformację'">DANE PODMIOTU SKŁADAJĄCEGO INFORMACJĘ</xsl:when>
				<xsl:when test="@rola='Składający informację'">DANE SKŁADAJĄCEGO INFORMACJĘ</xsl:when>
				<xsl:when test="@rola='Spadkodawca, Darczyńca lub inna osoba'">DANE SPADKODAWCY, DARCZYŃCY LUB INNEJ OSOBY (PODMIOTU), PO KTÓREJ LUB OD KTÓREJ ZOSTAŁY NABYTE RZECZY LUB PRAWA MAJĄTKOWE</xsl:when>
				<xsl:when test="@rola='Zainteresowany'">DANE ZAINTERESOWANEGO</xsl:when>
				<xsl:when test="@rola='Grupa Kapitałowa'">DANE PODATKOWEJ GRUPY KAPITAŁOWEJ</xsl:when>
				<xsl:when test="@rola='Obowiązany'">DANE OBOWIĄZANEGO</xsl:when>
				<xsl:when test="@rola='Podatnik'">DANE PODATNIKA</xsl:when>
				<xsl:when test="@rola='Platnik'">DANE PŁATNIKA&#xA0;</xsl:when>
				<xsl:when test="@rola='Płatnik'">DANE PŁATNIKA</xsl:when>
				<xsl:when test="@rola='Małżonek'">DANE MAŁŻONKA</xsl:when>
				<xsl:when test="@rola='Składający'">DANE SKŁADAJĄCEGO</xsl:when>
				<xsl:when test="@rola='Płatnik/Podmiot (Wypłacający Należność)'">DANE PŁATNIKA/PODMIOTU (WYPŁACAJĄCEGO NALEŻNOŚĆ)</xsl:when>
				<xsl:when test="@rola='Odbiorca Należności'">DANE PODATNIKA (ODBIORCY NALEŻNOŚCI)</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="@rola"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<div class="sekcja">
			<h2 class="tytul-sekcja-blok">
				<xsl:value-of select="$sekcja"/>&#xA0;<xsl:copy-of select="$tytul-sekcji"/>
			</h2>
			<xsl:apply-templates select="*[local-name()='OsobaFizyczna']
										| *[local-name()='OsobaNiefizyczna']
										| *[local-name()='OsobaFizZagr']
										| *[local-name()='OsobaNieFizZagr']">
				<xsl:with-param name="sekcja"/>
				<xsl:with-param name="wstaw-przed-ident" select="$wstaw-przed-ident"/>
				<xsl:with-param name="wstaw-za-ident" select="$wstaw-za-ident"/>
			</xsl:apply-templates>
			<xsl:if test="$pokazuj-adres">
				<xsl:apply-templates select="*[local-name()='AdresZamieszkania']
									 	| *[local-name()='AdresSiedziby']
									 	| *[local-name()='AdresZamieszkaniaSiedziby']
									 | *[local-name()='AdresPobytuNaTerytoriumRP']	">
					<xsl:with-param name="sekcja"/>
					<xsl:with-param name="wstaw-przed-adres" select="$wstaw-przed-adres"/>
					<xsl:with-param name="wstaw-za-adres" select="$wstaw-za-adres"/>
				</xsl:apply-templates>
			</xsl:if>
		</div>
	</xsl:template>
	<xsl:template match="*[local-name()='OsobaFizyczna']">
		<xsl:param name="sekcja"/>
		<xsl:param name="wstaw-przed-ident"/>
		<xsl:param name="wstaw-za-ident"/>
		<h3 class="tytul-sekcja-blok">
			<xsl:if test="$sekcja">
				<xsl:value-of select="$sekcja"/>&#xA0;
			</xsl:if>
			<xsl:text>Dane Identyfikacyjne</xsl:text>
		</h3>
		<xsl:copy-of select="$wstaw-przed-ident"/>
		<table class="normalna">
			<tr>
				<xsl:if test="*[local-name()='NIP' ]">
					<td class="wypelniane">
						<div class="opisrubryki"> Identyfikator podatkowy NIP</div>
						<xsl:apply-templates select="*[local-name() = 'NIP']"/>
					</td>
				</xsl:if>
				<xsl:if test="*[local-name()='PESEL' ]">
					<td class="wypelniane">
						<div class="opisrubryki">Identyfikator podatkowy numer PESEL</div>
						<xsl:apply-templates select="*[local-name() = 'PESEL']"/>
					</td>
				</xsl:if>
			</tr>
		</table>
		<table class="normalna">
			<tr>
				<td class="wypelniane" style="width:40%">
					<div class="opisrubryki">Nazwisko</div>
					<xsl:apply-templates select="*[local-name()='Nazwisko']"/>
				</td>
				<td class="wypelniane" style="width:40%">
					<div class="opisrubryki">Pierwsze imię</div>
					<xsl:apply-templates select="*[local-name()='ImiePierwsze']"/>
				</td>
				<td class="wypelniane" style="width:20%">
					<div class="opisrubryki">Data urodzenia</div>
					<xsl:apply-templates select="*[local-name()='DataUrodzenia']"/>
				</td>
			</tr>
		</table>
		<xsl:if test="*[local-name()='ImieOjca' or local-name()='ImieMatki' or local-name()='Obywatelstwo']">
			<table class="normalna">
				<tr>
					<xsl:if test="*[local-name()='ImieOjca' or local-name()='ImieMatki']">
						<td class="wypelniane">
							<div class="opisrubryki">Imię ojca</div>
							<xsl:apply-templates select="*[local-name() = 'ImieOjca']"/>
						</td>
						<td class="wypelniane">
							<div class="opisrubryki">Imię matki</div>
							<xsl:apply-templates select="*[local-name() = 'ImieMatki']"/>
						</td>
					</xsl:if>
					<xsl:if test="*[local-name()='Obywatelstwo']">
						<td class="wypelniane">
							<div class="opisrubryki">Obywatelstwo</div>
							<xsl:apply-templates select="*[local-name() = 'Obywatelstwo']"/>
						</td>
					</xsl:if>
				</tr>
			</table>
			<xsl:copy-of select="$wstaw-za-ident"/>
		</xsl:if>
	</xsl:template>
	<xsl:template match="*[local-name()='OsobaNiefizyczna']">
		<xsl:param name="sekcja"/>
		<xsl:param name="wstaw-przed-ident"/>
		<xsl:param name="wstaw-za-ident"/>
		<h3 class="tytul-sekcja-blok">
			<xsl:if test="$sekcja">
				<xsl:value-of select="$sekcja"/>&#xA0;
			</xsl:if>
			<xsl:text>Dane Identyfikacyjne</xsl:text>
		</h3>
		<xsl:copy-of select="$wstaw-przed-ident"/>
		<table class="normalna">
			<tr>
				<td class="wypelniane">
					<div class="opisrubryki">Identyfikator podatkowy NIP</div>
					<xsl:apply-templates select="*[local-name()='NIP']"/>
				</td>
				<xsl:if test="*[local-name()='REGON']">
					<td class="wypelniane">
						<div class="opisrubryki">REGON</div>
						<xsl:apply-templates select="*[local-name()='REGON']"/>
					</td>
				</xsl:if>
			</tr>
			<tr>
				<td colspan="2" class="wypelniane">
					<div class="opisrubryki">Nazwa pełna</div>
					<xsl:apply-templates select="*[local-name()='PelnaNazwa']"/>
				</td>
			</tr>
			<xsl:if test="*[local-name()='SkroconaNazwa']">
				<tr>
					<td colspan="2" class="wypelniane">
						<div class="opisrubryki">Nazwa skrócona</div>
						<xsl:apply-templates select="*[local-name()='SkroconaNazwa']"/>
					</td>
				</tr>
			</xsl:if>
		</table>
		<xsl:copy-of select="$wstaw-za-ident"/>
	</xsl:template>
	<xsl:template match="*[local-name()='OsobaFizZagr']">
		<xsl:param name="sekcja"/>
		<xsl:param name="wstaw-przed-ident"/>
		<xsl:param name="wstaw-za-ident"/>
		<h3 class="tytul-sekcja-blok">
			<xsl:if test="$sekcja">
				<xsl:value-of select="$sekcja"/>&#xA0;
			</xsl:if>
			<xsl:text>Dane Identyfikacyjne</xsl:text>
		</h3>
		<xsl:copy-of select="$wstaw-przed-ident"/>
		<table class="normalna">
			<tr>
				<td class="wypelniane" style="width:50%">
					<div class="opisrubryki">Nazwisko</div>
					<xsl:apply-templates select="*[local-name()='Nazwisko']"/>
				</td>
				<td class="wypelniane">
					<div class="opisrubryki">Pierwsze imię</div>
					<xsl:apply-templates select="*[local-name()='ImiePierwsze']"/>
				</td>
			</tr>
			<tr>
				<td class="wypelniane">
					<div class="opisrubryki">Imię ojca</div>
					<xsl:apply-templates select="*[local-name()='ImieOjca'] "/>
				</td>
				<td class="wypelniane">
					<div class="opisrubryki">Imię matki</div>
					<xsl:apply-templates select="*[local-name()='ImieMatki']"/>
				</td>
			</tr>
			<tr>
				<td class="wypelniane">
					<div class="opisrubryki" style="width:50%">Data urodzenia</div>
					<xsl:apply-templates select="*[local-name()='DataUrodzenia']"/>
				</td>
				<td class="wypelniane">
					<div class="opisrubryki">Kraj urodzenia</div>
					<xsl:apply-templates select="*[local-name()='KodKrajuUrodzenia']"/>
				</td>
			</tr>
			<tr>
				<td class="wypelniane" colspan="2">
					<div class="opisrubryki">Miejsce urodzenia</div>
					<xsl:apply-templates select="*[local-name()='MiejsceUrodzenia']"/>
				</td>
			</tr>
			<tr>
				<td class="wypelniane" style="width:50%">
					<div class="opisrubryki">Numer Identyfikacji Podatkowej</div>
					<xsl:apply-templates select="*[local-name()='NrIdTIN']"/>
				</td>
				<td class="wypelniane" style="width:50%">
					<div class="opisrubryki">Kraj wydania Numeru Identyfikacji Podatkowej</div>
					<xsl:apply-templates select="*[local-name()='KodkrajuWydaniaNrId']"/>
				</td>
			</tr>
			<tr>
				<td class="wypelniane" colspan="2">
					<div class="opisrubryki">Numer paszportu lub innego dokumentu stwierdzającego tożsamość</div>
					<xsl:apply-templates select="*[local-name()='NrDokumentuTozsamosci']"/>
				</td>
			</tr>
			<tr>
				<td class="wypelniane">
					<div class="opisrubryki">Rodzaj dokumentu</div>
					<xsl:choose>
						<xsl:when test="RodzajDokumentuTozsamosci='2'">2. dokument ubezpieczeniowy</xsl:when>
						<xsl:when test="RodzajDokumentuTozsamosci='3'">3. paszport</xsl:when>
						<xsl:when test="RodzajDokumentuTozsamosci='4'">4. urzędowy dokument stwierdzający tożsamość</xsl:when>
						<xsl:when test="RodzajDokumentuTozsamosci='8'">8. inny rodzaj identyfikacji podatkowej</xsl:when>
						<xsl:otherwise>9. inny dokument potwierdzający tożsamość</xsl:otherwise>
					</xsl:choose>
				</td>
				<td class="wypelniane">
					<div class="opisrubryki">Kraj wydania dokumentu wymienionego w poz.31</div>
					<xsl:apply-templates select="*[local-name()='KodKrajuWydaniaDokumentuTozsamosci']"/>
				</td>
			</tr>
		</table>
		<xsl:copy-of select="$wstaw-za-ident"/>
	</xsl:template>
	<xsl:template match="*[local-name()='OsobaNieFizZagr']">
		<xsl:param name="sekcja"/>
		<xsl:param name="wstaw-przed-ident"/>
		<xsl:param name="wstaw-za-ident"/>
		<h3 class="tytul-sekcja-blok">
			<xsl:if test="$sekcja">
				<xsl:value-of select="$sekcja"/>&#xA0;
			</xsl:if>
			<xsl:text>Dane Identyfikacyjne</xsl:text>
		</h3>
		<xsl:copy-of select="$wstaw-przed-ident"/>
		<table class="normalna">
			<tr>
				<td class="wypelniane">
					<div class="opisrubryki">Identyfikator podatkowy NIP</div>
					<xsl:apply-templates select="*[local-name()='NIP']"/>
				</td>
			</tr>
			<tr>
				<td class="wypelniane">
					<div class="opisrubryki">Nazwa pełna</div>
					<xsl:apply-templates select="*[local-name()='PelnaNazwa']"/>
				</td>
			</tr>
		</table>
		<table class="normalna">
			<tr>
				<td class="wypelniane">
					<div class="opisrubryki">Nazwa skrócona</div>
					<xsl:apply-templates select="*[local-name()='SkroconaNazwa']"/>
				</td>
				<td class="wypelniane">
					<div class="opisrubryki">Data rozpoczęcia działalności</div>
					<xsl:apply-templates select="*[local-name()='DataRozpoczeciaDzialalnosci']"/>
				</td>
			</tr>
		</table>
		<table class="normalna">
			<tr>
				<td class="wypelniane">
					<div class="opisrubryki">Rodzaj identyfikacji</div>
					<xsl:apply-templates select="*[local-name()='RodzajIdentyfikacji']"/>
				</td>
			</tr>
		</table>
		<table class="normalna">
			<tr>
				<td class="wypelniane">
					<div class="opisrubryki">Numer identyfikacyjny podatnika</div>
					<xsl:apply-templates select="*[local-name()='NumerIdentyfikacyjnyPodatnika']"/>
				</td>
				<td class="wypelniane">
					<div class="opisrubryki">Kod kraju wydania</div>
					<xsl:apply-templates select="*[local-name()='KodKrajuWydania']"/>
				</td>
			</tr>
		</table>
		<xsl:copy-of select="$wstaw-za-ident"/>
	</xsl:template>
	<xsl:template match="*[local-name()='AdresZamieszkania']">
		<xsl:param name="sekcja"/>
		<xsl:param name="wstaw-przed-adres"/>
		<xsl:param name="wstaw-za-adres"/>
		<h3 class="tytul-sekcja-blok">
			<xsl:if test="$sekcja">
				<xsl:value-of select="$sekcja"/>&#xA0;
			</xsl:if>
			<xsl:text>Adres Zamieszkania</xsl:text>
		</h3>
		<xsl:copy-of select="$wstaw-przed-adres"/>
		<xsl:choose>
			<xsl:when test="*[local-name()='AdresPol'] | *[local-name()='AdresZagr']">
				<xsl:apply-templates/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name="AdresTabela"/>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:copy-of select="$wstaw-za-adres"/>
	</xsl:template>
	<xsl:template match="*[local-name()='AdresSiedziby']">
		<xsl:param name="sekcja"/>
		<xsl:param name="wstaw-przed-adres"/>
		<xsl:param name="wstaw-za-adres"/>
		<h3 class="tytul-sekcja-blok">
			<xsl:if test="$sekcja">
				<xsl:value-of select="$sekcja"/>&#xA0;
			</xsl:if>
			<xsl:text>Adres Siedziby</xsl:text>
		</h3>
		<xsl:copy-of select="$wstaw-przed-adres"/>
		<xsl:choose>
			<xsl:when test="*[local-name()='AdresPol'] | *[local-name()='AdresZagr']">
				<xsl:apply-templates/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name="AdresTabela"/>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:copy-of select="$wstaw-za-adres"/>
	</xsl:template>
	<xsl:template match="*[local-name()='AdresZamieszkaniaSiedziby']">
		<xsl:param name="sekcja"/>
		<xsl:param name="wstaw-przed-adres"/>
		<xsl:param name="wstaw-za-adres"/>
		<h3 class="tytul-sekcja-blok">
			<xsl:if test="$sekcja">
				<xsl:value-of select="$sekcja"/>&#xA0;
			</xsl:if>
			<xsl:text>Adres Siedziby / Zamieszkania</xsl:text>
		</h3>
		<xsl:copy-of select="$wstaw-przed-adres"/>
		<xsl:choose>
			<xsl:when test="*[local-name()='AdresPol'] | *[local-name()='AdresZagr']">
				<xsl:apply-templates/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name="AdresTabela"/>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:copy-of select="$wstaw-za-adres"/>
	</xsl:template>
	<xsl:template match="*[local-name()='AdresPobytuNaTerytoriumRP']">
		<xsl:param name="sekcja"/>
		<xsl:param name="wstaw-przed-adres"/>
		<xsl:param name="wstaw-za-adres"/>
		<h3 class="tytul-sekcja-blok">
			<xsl:if test="$sekcja">
				<xsl:value-of select="$sekcja"/>&#xA0;
			</xsl:if>
			<xsl:text>Adres pobytu na terytorium RP</xsl:text>
		</h3>
		<xsl:copy-of select="$wstaw-przed-adres"/>
		<xsl:choose>
			<xsl:when test="*[local-name()='AdresPol'] | *[local-name()='AdresZagr']">
				<xsl:apply-templates/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name="AdresTabela"/>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:copy-of select="$wstaw-za-adres"/>
	</xsl:template>
	<xsl:template match="*[local-name()='AdresPol'] | *[local-name()='AdresZagr']" name="AdresTabela">
		<table class="normalna">
			<tr>
				<td class="wypelniane">
					<div class="opisrubryki">Kraj</div>
					<xsl:apply-templates select="*[local-name()='KodKraju']"/>
				</td>
				<td class="wypelniane" style="width:40%">
					<div class="opisrubryki">Województwo</div>
					<xsl:apply-templates select="*[local-name()='Wojewodztwo']"/>
				</td>
				<td class="wypelniane" style="width:40%">
					<div class="opisrubryki">Powiat</div>
					<xsl:apply-templates select="*[local-name()='Powiat']"/>
				</td>
			</tr>
		</table>
		<table class="normalna">
			<tr>
				<td class="wypelniane" style="width:35%">
					<div class="opisrubryki">Gmina</div>
					<xsl:apply-templates select="*[local-name()='Gmina']"/>
				</td>
				<td class="wypelniane">
					<div class="opisrubryki">Ulica</div>
					<xsl:apply-templates select="*[local-name()='Ulica']"/>
				</td>
				<td class="wypelniane" style="width:10%">
					<div class="opisrubryki">Numer domu</div>
					<xsl:apply-templates select="*[local-name()='NrDomu']"/>
				</td>
				<td class="wypelniane" style="width:10%">
					<div class="opisrubryki">Numer lokalu</div>
					<xsl:apply-templates select="*[local-name()='NrLokalu']"/>
				</td>
			</tr>
		</table>
		<table class="normalna">
			<tr>
				<td class="wypelniane">
					<div class="opisrubryki">Miejscowość</div>
					<xsl:apply-templates select="*[local-name()='Miejscowosc']"/>
				</td>
				<td class="wypelniane">
					<div class="opisrubryki">Kod pocztowy</div>
					<xsl:apply-templates select="*[local-name()='KodPocztowy']"/>
				</td>
				<xsl:if test="*[local-name()='Poczta']">
					<td class="wypelniane">
						<div class="opisrubryki">Poczta</div>
						<xsl:apply-templates select="*[local-name()='Poczta']"/>
					</td>
				</xsl:if>
			</tr>
		</table>
	</xsl:template>
	<xsl:template match="*[local-name()='KodKraju'] | *[local-name()='KodkrajuWydania']
							|*[local-name()='KodkrajuWydaniaNrId']
							|*[local-name()='KodKrajuUrodzenia'] | *[local-name()='P_D3']
							|*[local-name()='KodKrajuWydaniaDokumentuTozsamosci']" name="PokazKodKraju">
		<xsl:apply-templates/>&#xA0;
		<xsl:if test="$nazwy-dla-kodow">
			<span class="nazwa-dla-kodu">
				<xsl:text>(</xsl:text>
				<xsl:call-template name="ZnajdzWEnumeracji">
					<xsl:with-param name="schema" select="$schema-krajow"/>
					<xsl:with-param name="typ" select="'TKodKraju'"/>
					<xsl:with-param name="kod" select="text()"/>
				</xsl:call-template>
				<xsl:text>)</xsl:text>
			</span>
		</xsl:if>
	</xsl:template>
	<xsl:template match="*[local-name()='KodWaluty']" name="PokazKodWaluty">
		<xsl:apply-templates/>&#xA0;
		<xsl:if test="$nazwy-dla-kodow">
			<span class="nazwa-dla-kodu">
				<xsl:text>(</xsl:text>
				<xsl:call-template name="ZnajdzWEnumeracji">
					<xsl:with-param name="schema" select="$schema-walut"/>
					<xsl:with-param name="typ" select="'TKodWaluty'"/>
					<xsl:with-param name="kod" select="text()"/>
				</xsl:call-template>
				<xsl:text>)</xsl:text>
			</span>
		</xsl:if>
	</xsl:template>
	<xsl:template name="NaglowekTechniczny">
		<xsl:param name="uzycie"/>
		<!-- deklaracja | zalacznik -->
		<xsl:param name="naglowek"/>
		<xsl:param name="alternatywny-naglowek" select="$naglowek"/>
		<xsl:variable name="kod" select="$naglowek/*[local-name()='KodFormularza']"/>
		<xsl:variable name="kod2" select="$alternatywny-naglowek/*[local-name()='KodFormularza']"/>
		<xsl:variable name="wariant" select="$naglowek/*[local-name()='WariantFormularza']"/>
		<div class="naglowek">
			<table>
				<tr>
					<td colspan="2">
						<span class="kod-formularza">
							<xsl:apply-templates select="$kod"/>
						</span>
						<xsl:text>&#xA0;</xsl:text>
						<span class="wariant">(<xsl:apply-templates select="$wariant"/>)</span>
					</td>
				</tr>
				<tr>
					<td class="etykieta">Kod systemowy</td>
					<td class="wartosc">
						<xsl:value-of select="$kod/@kodSystemowy"/>
					</td>
				</tr>
				<xsl:call-template name="AtrybutNaglowka">
					<xsl:with-param name="etykieta">Kod podatku</xsl:with-param>
					<xsl:with-param name="pierwszy" select="$kod/@kodPodatku"/>
					<xsl:with-param name="drugi" select="$kod2/@kodPodatku"/>
				</xsl:call-template>
			</table>
		</div>
	</xsl:template>
	<xsl:template name="AtrybutNaglowka">
		<xsl:param name="etykieta"/>
		<xsl:param name="pierwszy"/>
		<xsl:param name="drugi"/>
		<xsl:variable name="wartosc">
			<xsl:choose>
				<xsl:when test="$pierwszy">
					<xsl:value-of select="$pierwszy"/>
				</xsl:when>
				<xsl:when test="$drugi">
					<xsl:value-of select="$drugi"/>
				</xsl:when>
			</xsl:choose>
		</xsl:variable>
		<xsl:if test="string-length($wartosc) > 0">
			<tr>
				<td class="etykieta">
					<xsl:copy-of select="$etykieta"/>
				</td>
				<td class="wartosc">
					<xsl:value-of select="$wartosc"/>
				</td>
			</tr>
		</xsl:if>
	</xsl:template>
	<xsl:template name="NaglowekTytulowy">
		<xsl:param name="naglowek"/>
		<xsl:param name="nazwa"/>
		<xsl:param name="objasnienie"/>
		<xsl:param name="podstawy-prawne"/>
		<xsl:param name="uzycie"/>
		<xsl:param name="nad-data"/>
		<xsl:param name="przed-data"/>
		<xsl:param name="po-dacie"/>
		<!-- deklaracja | zalacznik -->
		<div>
			<xsl:choose>
				<xsl:when test="$uzycie = 'deklaracja'">
					<xsl:attribute name="class">tlo-formularza</xsl:attribute>
				</xsl:when>
				<xsl:when test="$uzycie = 'zalacznik'">
					<xsl:attribute name="class">tlo-zalacznika</xsl:attribute>
				</xsl:when>
			</xsl:choose>
			<xsl:if test="$nazwa">
				<h1 class="nazwa">
					<xsl:copy-of select="$nazwa"/>
				</h1>
			</xsl:if>
			<xsl:copy-of select="$nad-data"/>
			<xsl:if test="$naglowek">
				<div class="okres">
					<xsl:if test="$przed-data or $po-dacie">
						<span class="obok-daty">
							<xsl:copy-of select="$przed-data"/>
						</span>
					</xsl:if>
					<xsl:apply-templates select="$naglowek/*[local-name()='Miesiac'] | $naglowek/*[local-name()='Kwartal']"/>
					<xsl:apply-templates select="$naglowek/*[local-name()='Rok']"/>
					<xsl:apply-templates select="$naglowek/*[local-name()='OkresOd']"/>
					<xsl:apply-templates select="$naglowek/*[local-name()='OkresDo']"/>
					<xsl:apply-templates select="$naglowek/*[local-name()='Data']"/>
					<xsl:if test="$przed-data or $po-dacie">
						<span class="obok-daty">
							<xsl:copy-of select="$po-dacie"/>
						</span>
					</xsl:if>
				</div>
			</xsl:if>
			<xsl:if test="$objasnienie">
				<div class="objasnienie">
					<xsl:copy-of select="$objasnienie"/>
				</div>
			</xsl:if>
		</div>
		<xsl:if test="$podstawy-prawne">
			<div class="prawne">
				<xsl:copy-of select="$podstawy-prawne"/>
			</div>
		</xsl:if>
	</xsl:template>
	<xsl:template name="NaglowekTytulowyZalacznik">
		<xsl:param name="naglowek"/>
		<xsl:param name="nazwa"/>
		<xsl:param name="objasnienie"/>
		<xsl:param name="podstawy-prawne"/>
		<xsl:param name="uzycie"/>
		<xsl:param name="nad-data"/>
		<xsl:param name="przed-data"/>
		<xsl:param name="po-dacie"/>
		<!-- deklaracja | zalacznik -->
		<div>
			<xsl:choose>
				<xsl:when test="$uzycie = 'deklaracja'">
					<xsl:attribute name="class">tlo-formularza</xsl:attribute>
				</xsl:when>
				<xsl:when test="$uzycie = 'zalacznik'">
					<xsl:attribute name="class">tlo-zalacznika</xsl:attribute>
				</xsl:when>
			</xsl:choose>
			<xsl:if test="$nazwa">
				<h1 class="nazwa">
					<xsl:copy-of select="$nazwa"/>
				</h1>
			</xsl:if>
			<xsl:copy-of select="$nad-data"/>
			<xsl:if test="$naglowek">
				<div class="okres">
					<xsl:if test="$przed-data or $po-dacie">
						<span class="obok-daty">
							<xsl:copy-of select="$przed-data"/>
						</span>
					</xsl:if>
					<xsl:apply-templates select="$naglowek/*[local-name()='Miesiac'] | $naglowek/*[local-name()='Kwartal']"/>
					<xsl:apply-templates select="$naglowek/*[local-name()='Rok']"/>
					<xsl:apply-templates select="$naglowek/*[local-name()='OkresOd']"/>
					<xsl:apply-templates select="$naglowek/*[local-name()='OkresDo']"/>
					<xsl:apply-templates select="$naglowek/*[local-name()='Data']"/>
					<xsl:if test="$przed-data or $po-dacie">
						<span class="obok-daty">
							<xsl:copy-of select="$po-dacie"/>
						</span>
					</xsl:if>
				</div>
			</xsl:if>
			<xsl:if test="$objasnienie">
				<div class="objasnienie">
					<xsl:copy-of select="$objasnienie"/>
				</div>
			</xsl:if>
		</div>
		<xsl:if test="$podstawy-prawne">
			<div class="prawne">
				<xsl:copy-of select="$podstawy-prawne"/>
			</div>
		</xsl:if>
	</xsl:template>
	<xsl:template match="*[local-name()='Naglowek']/*[local-name()='Miesiac']">
		<span class="data">
			<span class="opisrubryki">
				<xsl:call-template name="WezNumerPozycji"/>
				<xsl:text>Miesiąc&#xA0;&#xA0;</xsl:text>
			</span>
			<xsl:apply-templates/>
		</span>
	</xsl:template>
	<xsl:template match="*[local-name()='Naglowek']/*[local-name()='Kwartal']">
		<span class="data">
			<span class="opisrubryki">
				<xsl:call-template name="WezNumerPozycji"/>
				<xsl:text>Kwartał&#xA0;&#xA0;</xsl:text>
			</span>
			<xsl:apply-templates/>
		</span>
	</xsl:template>
	<xsl:template match="*[local-name()='Naglowek']/*[local-name()='Rok']">
		<span class="data">
			<span class="opisrubryki">
				<xsl:call-template name="WezNumerPozycji"/>
				<xsl:text>Rok&#xA0;&#xA0;</xsl:text>
			</span>
			<xsl:apply-templates/>
		</span>
	</xsl:template>
	<xsl:template match="*[local-name()='Naglowek']/*[local-name()='OkresOd']">
		za okres&#xA0;<span class="data">
			<span class="opisrubryki">
				<xsl:call-template name="WezNumerPozycji"/>
			</span>
			<xsl:text>od&#xA0;</xsl:text>
			<xsl:apply-templates/>
		</span>
	</xsl:template>
	<xsl:template match="*[local-name()='Naglowek']/*[local-name()='OkresDo']">
		&#xA0;<span class="data">
			<span class="opisrubryki">
				<xsl:call-template name="WezNumerPozycji"/>
			</span>
			<xsl:text>do&#xA0;</xsl:text>
			<xsl:apply-templates/>
		</span>
	</xsl:template>
	<xsl:template match="*[local-name()='Naglowek']/*[local-name()='Data']">
		<span class="data">
			<span class="opisrubryki">
				<xsl:call-template name="WezNumerPozycji"/>
				<xsl:text>Data&#xA0;&#xA0;</xsl:text>
			</span>
			<xsl:apply-templates/>
		</span>
	</xsl:template>
	<xsl:template name="WezNumerPozycji">
		<xsl:if test="a">
			<xsl:value-of select="substring(@poz, 3)"/>
			<xsl:text>.</xsl:text>
		</xsl:if>
	</xsl:template>
	<xsl:template name="MiejsceICel">
		<xsl:param name="sekcja"/>
		<h2 class="tytul-sekcja-blok">
			<xsl:value-of select="$sekcja"/>&#xA0;MIEJSCE I CEL SKŁADANIA</h2>
		<table class="normalna">
			<tr>
				<td class="niewypelnianeopisy" style="width:33%">Kod i nazwa urzędu skarbowego, do którego adresowany jest dokument</td>
				<td class="wypelniane" style="width:auto">
					<xsl:apply-templates select="*[local-name()='Naglowek']/*[local-name()='KodUrzedu']"/>
				</td>
			</tr>
			<tr>
				<td class="niewypelnianeopisy">Cel złożenia formularza</td>
				<td class="wypelniane">
					<xsl:choose>
						<xsl:when test="*[local-name()='Naglowek']/*[local-name()='CelZlozenia'] =1">
							<input type="checkbox" checked="checked" disabled="disabled"/>1. złożenie
						</xsl:when>
						<xsl:when test="*[local-name()='Naglowek']/*[local-name()='CelZlozenia'] =2">
							<input type="checkbox" checked="checked" disabled="disabled"/>2. korekta
						</xsl:when>
					</xsl:choose>
				</td>
			</tr>
		</table>
	</xsl:template>
	<xsl:template match="*[local-name()='Naglowek']/*[local-name()='KodUrzedu'] | *[local-name()='Naglowek']/*[local-name()='PoprzedniNaczelnikUS'] ">
		<xsl:apply-templates/>&#xA0;
		<xsl:if test="$nazwy-dla-kodow">
			<span class="nazwa-dla-kodu">
				<xsl:call-template name="ZnajdzWEnumeracji">
					<xsl:with-param name="schema" select="$schema-urzedow"/>
					<xsl:with-param name="typ" select="'TKodUS'"/>
					<xsl:with-param name="kod" select="text()"/>
				</xsl:call-template>
			</span>
		</xsl:if>
	</xsl:template>
	<xsl:template name="KrajUzyskaniaDochodu">
		<xsl:apply-templates/>&#xA0;
		<xsl:if test="$nazwy-dla-kodow">
			<span class="nazwa-dla-kodu">
				<xsl:text>(</xsl:text>
				<xsl:call-template name="ZnajdzWEnumeracji">
					<xsl:with-param name="schema" select="$schema-krajow"/>
					<xsl:with-param name="typ" select="'TKodKraju'"/>
					<xsl:with-param name="kod" select="text()"/>
				</xsl:call-template>
				<xsl:text>)</xsl:text>
			</span>
		</xsl:if>
	</xsl:template>
	<xsl:template name="PouczeniaKoncowe">
		<xsl:param name="sekcja"/>
		<xsl:param name="etykieta"/>
		<xsl:if test="*[local-name()='Pouczenie' or local-name()='Pouczenie1' or local-name()='Pouczenie2']">
			<h2 class="tekst">*) Pouczenie</h2>
			<xsl:for-each select="*[local-name()='Pouczenie' or local-name()='Pouczenie1' or local-name()='Pouczenie2']">
				<div class="pouczenie">
					<xsl:apply-templates/>
				</div>
			</xsl:for-each>
		</xsl:if>
		<xsl:if test="*[local-name()='Oswiadczenie']">
			<h2 class="tytul-sekcja-blok">
				<xsl:value-of select="$sekcja"/>&#xA0;<xsl:copy-of select="$etykieta"/>
			</h2>
			<table class="pouczenia">
				<tr>
					<td>
						<xsl:apply-templates select="*[local-name()='Oswiadczenie']"/>
					</td>
				</tr>
			</table>
			<div class="lamstrone"/>
		</xsl:if>
	</xsl:template>
	<xsl:template name="PozycjaSzczegolowa">
		<xsl:param name="element"/>
		<xsl:param name="prefiks" select="'P_'"/>
		<xsl:param name="etykieta"/>
		<xsl:variable name="nazwa">
			<xsl:choose>
				<xsl:when test="@poz">
					<xsl:value-of select="@poz"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="local-name($element)"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="numer">
			<xsl:choose>
				<xsl:when test="starts-with($nazwa, $prefiks)">
					<xsl:value-of select="substring-after($nazwa, $prefiks)"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="''"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<div class="opisrubryki">
			<xsl:value-of select="$numer"/>
			<xsl:text>.</xsl:text>
			<xsl:if test="$etykieta">&#xA0;<xsl:copy-of select="$etykieta"/>
			</xsl:if>
		</div>
		<xsl:apply-templates select="$element"/>
	</xsl:template>
	<xsl:template name="PozycjaSzczegolowa2">
		<xsl:param name="prefiks" select="'P_'"/>
		<xsl:param name="numer"/>
		<xsl:param name="etykieta"/>
		<xsl:variable name="nazwa" select="concat($prefiks, $numer)"/>
		<div class="opisrubryki">
			<xsl:value-of select="$numer"/>
			<xsl:text>.</xsl:text>
			<xsl:if test="$etykieta">&#xA0;<xsl:copy-of select="$etykieta"/>
			</xsl:if>
		</div>
		<xsl:apply-templates select="*[local-name() = $nazwa]"/>
	</xsl:template>
	<xsl:template name="TakNie">
		<xsl:param name="element"/>
		<xsl:choose>
			<xsl:when test="$element">tak</xsl:when>
			<xsl:otherwise>nie</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<xsl:template name="TakNie12">
		<xsl:choose>
			<xsl:when test=".='1'">
				<input type="checkbox" checked="checked" disabled="disabled"/>1. tak
			</xsl:when>
			<xsl:when test=".='2'">
				<input type="checkbox" checked="checked" disabled="disabled"/>2. nie
			</xsl:when>
		</xsl:choose>
	</xsl:template>
	<xsl:template name="ZnajdzWEnumeracji">
		<xsl:param name="schema"/>
		<xsl:param name="typ"/>
		<xsl:param name="kod"/>
		<xsl:variable name="wschema" select="document($schema)"/>
		<xsl:value-of select="$wschema//xs:simpleType[@name=$typ]//
			xs:enumeration[@value = $kod]//xs:documentation"/>
	</xsl:template>
	<xsl:template name="StyleWspolne">
		<style type="text/css"><![CDATA[
body {
	background-color: #FFFFFF;
	color: #000000;
	font-family: 'Arial', sans-serif;
	font-size: 11pt;
	margin: 0;
	padding: 1px 5%;
}

div.body {
	width: 100%;
	min-width: 480px;
	margin-left: auto;
	margin-right: auto;
}

div.deklaracja, div.zalacznik {
	margin: 2em 0;
}

.tlo-zalacznika {
	background-color: #FFFFDD;
}

table {
	border-collapse: collapse;
}

.normalna, .tytul-sekcja-blok {
	width: 100%;
}

.naglowek {
	background-color: #CCDDFF;
}

.kod-formularza {
	font-size: 2em;
	font-weight: bold;
}

.naglowek .wartosc {
	font-weight: bold;
}

.tytul {
	font-size: 2em;
	font-weight: bold;
	text-align: center;
}

.tytulformularza {
	font-size: xx-large;
	font-weight: bold;
	text-align: center;
}

.okres {
	display: block;
	margin: 1em;
	font-size: 1.2em;
	text-align: center;
	vertical-align: top;
	clear: both;
}

.data {
	border: 1px solid black;
	padding: 2px 1.5em;
	background-color: white;
	font-weight: bold;
	margin: 0 2em;
}

.obok-daty {
	text-align: right;
	display: inline-block;
	width: 45%;
}

.objasnienie {
	border: 2px solid black;
	padding: 0.25em 0.5em;
	font-size: 0.8em;
}

.zalacznik-objasnienie {
	background-color: #DDDDDD;
	border: 2px solid black;
	font-size: 0.8em;
	width:99.5%;
}

.prawne {
	background-color: #DDDDDD;
	border: 2px solid black;
	font-size: 0.8em;
}

.prawne .etykieta {
	min-width: 9em;
}

.wypelniane {
	background-color: white;
}

.niewypelniane, .ukryte {
	background-color: #DDDDDD;
}

.pouczenia td {
	background-color: white;
	border: 2px solid black;
}

.tytul-sekcja-blok {
	background-color: #DDDDFF;
	border: 2px solid black;
	text-transform: uppercase;
	width: 99.5%;
}


h1 {
	font-size: 1.4em;
	font-weight: bold;
	text-align: center;
	text-transform: uppercase;
}

h2 {
	text-align: left;
	font-size: 1.2em;
	font-weight: bold;
}

h3 {
	text-align: left;
	font-size: 1.2em;
	font-weight: normal;
}

h4 {
	text-align: left;
	font-size: 1em;
	font-weight: normal;
}

h1, h2, h3, h4 {
	font-family: 'Arial', sans-serif;
	margin: 0;
	padding: 1px;
}

.wypelniane {
	border: 1px solid black;
	font-size: 1.2em;
	padding: 1px;
	vertical-align: top;
	text-align: left;
}


.puste {
	background-color: #DDDDDD;
	border: 1px solid black;
	font-size: 0.8em;
	padding: 1px;
	height: 2em;
	vertical-align: top;
}

.puste2 {
	background-color: #DDDDDD;
	border: 1px solid black;
	 font-size: 1.2em;
	padding: 1px;
	height: 2em;
	text-align: center;
}

.niewypelnianeopisy {
	background-color: #DDDDDD;
	border: 1px solid black;
	font-size: 0.8em;
	padding: 1px;
	height: 2em;
	vertical-align: top;
	text-align: left;
}

.center {
	background-color: #DDDDDD;
	border: 1px solid black;
	font-size: 0.8em;
	padding: 1px;
	height: 2em;
	vertical-align: top;
	text-align: center;
}

.niewypelniane, .pouczenia td, .taknie {
	border: 1px solid black;
	font-size: 0.8em;
	font-weight: bold;
	padding: 1px;
	height: 2em;
	vertical-align: top;
	text-align: center;
}

.kwota {
	text-align: right;
	padding-right: 0.2em;
}

.opisrubryki {
	font-size: 0.5em;
	margin-bottom: 0.2em;
	text-align: left;
	font-weight: bold;
	text-transform: none;
}

.opis-tekstowy{
	font-size: 0.7em;
	margin-bottom: 0.2em;
	font-weight: bold;
	text-transform: none;
}

.czcionka td, .czcionka th {
	font-size: 0.9em;
	height: 1em;
}

.nazwa-dla-kodu {
	font-size: 0.9em;
}

table.normalna, table.pouczenia, table.sposob-opodatkowania {
	width: 100%;
	margin: 0;
	border: 1px solid black;
}

h2.tekst {
	text-align: center;
	margin: 0.5em auto;
}

.pouczenie {
	padding: 0.5em 2em;
	text-align: center;
}

p {
	padding: 0;
	margin: 0.2em 0;
}

.objasnienie ol {
	list-style-type: decimal;
}

.objasnienie ol ul {
	list-style-type: disc;
}

.taknie {
	text-transform: uppercase;
	text-align: center;
}

.normalna-tekstowa {
	width: 100%;
	border: 0px
}

 .tekst {
	text-align: center;
}

.wartosc {
	vertical-align: top;
}

.miesiac {
	border: 1px solid black;
	font-size: 0.8em;
	font-weight: bold;
	padding: 1px;
	height: 2em;
	vertical-align: middle;
	text-align: center;
	background-color: #DDDDDD;
}

.podtytul {
	font-size: medium;
}

.tytulzalacznika {
	font-size: x-large;
	font-weight: bold;
	text-align: center;
}

.opis {
	font-size: 1em;
	padding: 4px;
}

.opis-tabela {
	font-size: 1em;
	padding: 4px;
	border: 0;
}

.dodatkowe {
	background-color: white;
	border: 0;
}

.wypunktowane {
	font-size: 1em;
	padding: 1px;
	vertical-align: top;
}

.tlo-formularza, .tlo-zalacznika {
	padding-bottom: 1px;
}

@media print {
	.lamstrone {
		page-break-before: always;
	}

	.sekcja {
		page-break-inside: avoid;
	}
}]]></style>
	</xsl:template>
</xsl:stylesheet>
