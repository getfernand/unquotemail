# -*- coding:utf-8 -*-

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
import html2text, tempfile, re, markdown

"""
From:
    @see https://github.com/crisp-oss/email-reply-parser/blob/master/lib/regex.js
    @see https://github.com/mailgun/talon/blob/master/talon/quotations.py
"""

patterns = [
    # English
    # On DATE, NAME <EMAIL> wrote:
    # Original pattern: /^-*\s*(On\s.+\s.+\n?wrote:{0,1})\s{0,1}-*$/m
    re.compile(
        r"^-*\s*(({})\s.+\s.+\n?({})\s*:)\s?-*".format(
            '|'.join(('on', 'le', 'el', 'il', 'em')),
            '|'.join(('wrote', 'sent', 'écrit', 'escribió', 'scritto', 'escreveu'))
        ),
        re.MULTILINE | re.IGNORECASE
    ),

    # German
    # Am DATE schrieb NAME <EMAIL>:
    # Original pattern: /^\s*(Am\s.+\s)\n?\n?schrieb.+\s?(\[|<).+(\]|>):$/m
    re.compile(r"^\s*(am\s.+\s)\n?\n?schrieb.+\s?(\[|<).+(\]|>):", re.MULTILINE | re.IGNORECASE),

    # Dutch
    # Il DATE, schreef NAME <EMAIL>:
    # Original pattern: /^\s*(Op\s[\s\S]+?\n?schreef[\s\S]+:)$/m
    re.compile(r"^\s*(op\s[\s\S]+?\n?(schreef|verzond|geschreven)[\s\S]+:)", re.MULTILINE | re.IGNORECASE),

    # Polish
    # W dniu DATE, NAME <EMAIL> pisze|napisał:
    # Original pattern: /^\s*((W\sdniu|Dnia)\s[\s\S]+?(pisze|napisał(\(a\))?):)$/mu
    re.compile(r"^\s*((w\sdniu|dnia)\s[\s\S]+?(pisze|napisał(\(a\))?):)", re.MULTILINE | re.IGNORECASE),

    # Swedish, Danish
    # Den DATE skrev NAME <EMAIL>:
    # Original pattern: /^\s*(Den\s.+\s\n?skrev\s.+:)$/m
    re.compile(r'^\s*(den|d.)?\s?.+\s?skrev\s?\".+\"\s*[\[|<].+[\]|>]\s?:', re.MULTILINE | re.IGNORECASE),  # Outlook 2019 (da)

    # Vietnamese
    # Vào DATE đã viết NAME <EMAIL>:
    re.compile(r"^\s*(vào\s.+\s\n?đã viết\s.+:)", re.MULTILINE | re.IGNORECASE),

    # Outlook 2019 (cz)
    re.compile(r'^\s?dne\s?.+\,\s?.+\s*[\[|<].+[\]|>]\s?napsal\(a\)\s?:', re.MULTILINE | re.IGNORECASE),

    # Outlook 2019 (ru)
    re.compile(r'^\s?.+\s?пользователь\s?\".+\"\s*[\[|<].+[\]|>]\s?написал\s?:', re.MULTILINE | re.IGNORECASE),

    # Outlook 2019 (sk)
    re.compile(r'^\s?.+\s?používateľ\s?.+\s*\([\[|<].+[\]|>]\)\s?napísal\s?:', re.MULTILINE | re.IGNORECASE),

    # Outlook 2019 (tr)
    re.compile(r'^\s?\".+\"\s*[\[|<].+[\]|>]\,\s?.+\s?tarihinde şunu yazdı\s?:', re.MULTILINE | re.IGNORECASE),

    # Outlook 2019 (hu)
    re.compile(r'^\s?.+\s?időpontban\s?.+\s*[\[|<|(].+[\]|>|)]\s?ezt írta\s?:', re.MULTILINE | re.IGNORECASE),

    # ----------------------------

    # pe DATE NAME <EMAIL> kirjoitti:
    # Original pattern: /^\s*(pe\s.+\s.+\n?kirjoitti:)$/m
    re.compile(r"^\s*(pe\s.+\s.+\n?kirjoitti:)", re.MULTILINE | re.IGNORECASE),

    # > 在 DATE, TIME, NAME 写道：
    # Original pattern: /^(在[\s\S]+写道：)$/m
    re.compile(r"^(在[\s\S]+写道：)", re.MULTILINE),

    # NAME <EMAIL> schrieb:
    # Original pattern: /^(.+\s<.+>\sschrieb:)$/m
    re.compile(r"^(.+\s<.+>\sschrieb\s?:)", re.MULTILINE | re.IGNORECASE),

    # NAME on DATE wrote:
    # Original pattern: /^(.+\son.*at.*wrote:)$/m
    re.compile(r"^(.+\son.*at.*wrote:)", re.MULTILINE | re.IGNORECASE),

    # "From: NAME <EMAIL>" OR "From : NAME <EMAIL>" OR "From : NAME<EMAIL>"
    # Original pattern: /^\s*(From\s?:.+\s?\n?\s*[\[|<].+[\]|>])/m
    re.compile(
        r"^\s*(({})\s?:.+\s?\n?\s*(\[|<).+(\]|>))".format(
            '|'.join(('from', 'van', 'de', 'von', 'da'))
        ),
        re.MULTILINE | re.IGNORECASE
    ),

    ##########################
    # Date starting patterns #
    ##########################

    # DATE TIME NAME 작성:
    # Original pattern: /^(20[0-9]{2}\..+\s작성:)$/m
    re.compile(r"^(20[0-9]{2}\..+\s작성:)$", re.MULTILINE),

    # DATE TIME、NAME のメッセージ:
    # Original pattern: /^(20[0-9]{2}\/.+のメッセージ:)$/m
    re.compile(r"^(20[0-9]{2}\/.+のメッセージ:)", re.MULTILINE),

    # 20YY-MM-DD HH:II GMT+01:00 NAME <EMAIL>:
    # Original pattern: /^(20[0-9]{2})-([0-9]{2}).([0-9]{2}).([0-9]{2}):([0-9]{2})\n?(.*)>:$/m
    re.compile(r"^(20[0-9]{2})-([0-9]{2}).([0-9]{2}).([0-9]{2}):([0-9]{2})\n?(.*)>:", re.MULTILINE),

    # DD.MM.20YY HH:II NAME <EMAIL>
    # Original pattern: /^([0-9]{2}).([0-9]{2}).(20[0-9]{2})(.*)(([0-9]{2}).([0-9]{2}))(.*)\"( *)<(.*)>( *):$/m
    re.compile(r"^([0-9]{2}).([0-9]{2}).(20[0-9]{2})(.*)(([0-9]{2}).([0-9]{2}))(.*)\"( *)<(.*)>( *):", re.MULTILINE),

    # HH:II, DATE, NAME <EMAIL>:
    # Original pattern: /^[0-9]{2}:[0-9]{2}(.*)[0-9]{4}(.*)\"( *)<(.*)>( *):$/
    re.compile(r"^[0-9]{2}:[0-9]{2}(.*)[0-9]{4}(.*)\"( *)<(.*)>( *):", re.MULTILINE),

    # 02.04.2012 14:20 пользователь "bob@example.com" <bob@xxx.mailgun.org> написал:
    re.compile(r"(\d+/\d+/\d+|\d+\.\d+\.\d+).*\s\S+@\S+:", re.S),

    # 2014-10-17 11:28 GMT+03:00 Bob <bob@example.com>:
    re.compile(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+GMT.*\s\S+@\S+:", re.S | re.IGNORECASE),

    # Thu, 26 Jun 2014 14:00:51 +0400 Bob <bob@example.com>:
    re.compile(r'\S{3,10}, \d\d? \S{3,10} 20\d\d,? \d\d?:\d\d(:\d\d)?( \S+){3,6}@\S+:'),

    ############################
    # Dash Delimiters patterns #
    ############################

    # English
    # Original Message delimiter
    # Original pattern: /^-{1,12} ?(O|o)riginal (M|m)essage ?-{1,12}$/i,
    re.compile(
        r"^>?\s*-{{3,12}}\s*({})\s*-{{3,12}}\s*".format(
            '|'.join((
                'original message', 'reply message', 'original text', "message d'origine",
                'original email', 'ursprüngliche nachricht', 'original meddelelse',
                'original besked', 'original message', 'original meddelande',
                'originalbericht', 'originalt meddelande', 'originalt melding',
                'alkuperäinen viesti', 'alkuperäinen viesti', 'originalna poruka',
                'originalna správa', 'originálna správa', 'originální zpráva',
                'původní zpráva', 'antwort nachricht', 'oprindelig besked', 'oprindelig meddelelse'
            ))
        ),
        re.MULTILINE | re.IGNORECASE
    ),
]


class Unquote:
    def __init__(self, html, text, sender=None, parse=True):
        self.html = html.replace('\xa0', ' ') if html else None
        self.text = text.replace('\xa0', ' ') if text else None

        if not self.html and not self.text:
            raise ValueError('You must provide at least one of html or text')

        self.sender = None
        if sender:
            self.sender = sender.strip('<> \t\r\n')

        if parse:
            self.parse()

    def get_html(self):
        return self.html

    def get_text(self):
        return self.text

    def _parse_structure(self, soup):
        # Moz (must be before Apple)
        moz = soup.find('div', attrs={'class': 'moz-cite-prefix'})
        if moz:
            next_sibling = moz.find_next('blockquote', attrs={'type': 'cite'})
            if next_sibling:
                next_sibling.decompose()
                moz.decompose()
                return True

        # Freshdesk
        freshdesk = soup.find('div', class_='freshdesk_quote')
        if freshdesk:
            freshdesk.decompose()
            return True

        # Front
        front = soup.find(class_='front-blockquote')
        if front:
            front.decompose()
            return True

        # Spark
        spark = soup.find(attrs={'name': 'messageReplySection'})
        if spark:
            spark.decompose()
            return True

        # Gmail
        gmail = soup.find(class_='gmail_quote')
        if gmail:
            gmail.decompose()
            return True

        # Yahoo
        yahoo = soup.find('div', class_='yahoo_quoted')
        if yahoo:
            yahoo.decompose()
            return True

        # Ymail
        ymail = soup.find('div', class_='ymail_android_signature')
        if ymail:
            ymail.decompose()
            return True

        # Intercom
        intercom = soup.find('div', class_='history')
        if intercom:
            intercom.decompose()
            return True

        # MsOffice
        msoffice = soup.find('div', id='mail-editor-reference-message-container')
        if msoffice:
            msoffice.decompose()
            return True

        # MsOutlook
        msoutlook = soup.select_one('div[style^="border:none;border-top:solid"]>p.MsoNormal>b')
        if msoutlook:
            mso_root = msoutlook.parent.parent
            if mso_root and mso_root['style'].replace('cm', 'in').replace('pt', 'in').replace('mm', 'in').endswith(' 1.0in;padding:3.0in 0in 0in 0in'):
                if len([x for x in mso_root.parent.contents if str(x).startswith('<')]) == 1:
                    mso_root = mso_root.parent

                pending_removal = []
                for ns in mso_root.next_siblings:
                    if not isinstance(ns, NavigableString):
                        pending_removal.append(ns)

                for pr in pending_removal:
                    pr.decompose()

                mso_root.decompose()
                return True

        # Outlook
        outlook = soup.find('div', id='divRplyFwdMsg')
        if outlook:
            for p in outlook.previous_siblings:
                if isinstance(p, Tag):
                    if p.name == 'hr':
                        # It is a reply from Outlook! We clear!
                        for sibling in list(outlook.next_siblings):
                            if isinstance(sibling, NavigableString):
                                sibling.extract()
                            else:
                                sibling.decompose()

                        outlook.decompose()
                        p.decompose()
                    return True

        # ProtonMail
        proton = soup.find(class_='protonmail_quote')
        if proton:
            proton.decompose()
            return True

        # Trix
        trix = soup.select_one('div.trix-content>blockquote')
        if trix:
            trix.decompose()
            return True

        # ZMail
        zmail = soup.find('div', class_="zmail_extra")
        if zmail:
            previous = next(zmail.previous_siblings)
            if previous.attrs.get('class') and 'zmail_extra_hr' in previous.attrs['class']:
                previous.decompose()

            zmail.decompose()
            return True

        # Zoho
        zoho = soup.find('div', title='beforequote:::')
        if zoho:
            for ns in zoho.next_siblings:
                if not isinstance(ns, NavigableString):
                    ns.decompose()

            if zoho.previous_sibling.text.strip().startswith('---'):
                zoho.previous_sibling.decompose()

            zoho.decompose()
            return True

        # QT
        qt = soup.find('blockquote', attrs={'type': 'cite', 'id': 'qt'})
        if qt:
            qt.decompose()
            return True

        # Apple and generic
        generic = soup.find('blockquote', attrs={'type': 'cite'})
        if generic:
            for elt in generic.find_all_next():
                if not isinstance(elt, NavigableString):
                    if elt and elt.string:
                        elt.decompose()

            generic.decompose()
            return True

        # Custom A
        custom_a = soup.find('div', class_="quote")
        if custom_a and custom_a.get('style') and custom_a['style'].replace(' ', '').find('border:none;') > -1:
            custom_a.decompose()
            return True

        # Custom B
        custom_b = soup.select_one('div.quote>blockquote')
        if custom_b and custom_b.attrs and custom_b.attrs.get('style') and custom_b.attrs.get('style').lower().find('font-style'):
            custom_b.parent.parent.parent.decompose()
            return True

    def _clear_text(self, text):
        for pattern in ('>', '<', ' ', '\n', '\r', '\t', '\xa0'):
            text = text.replace(pattern, '')

        return text.strip()

    def parse(self):
        """
        1. Class based signatures
        The first thing we do is try to locate specific classes for each specific mail provider.
        For that, we rely on the sender message_id to identify the provider and remove the appropriate class whenever possible
        """
        if self.html:
            soup = BeautifulSoup(self.html, 'html.parser')
            if self._parse_structure(soup):
                self.html = str(soup).strip()
                self.text = html2text.html2text(self.html).strip()
                return True

            """
            1a. Try to locate any class="*quote*" and debug it
            """
            quote = soup.select('[class*="quote"]')
            if quote:
                self.quote_found(soup)

            """
            1b. Try to locate any class="*sign*" and debug it
            """
            quote = soup.select('[class*="sign"]')
            if quote:
                self.sign_found(soup)

        if not self.text:
            self.text = html2text.html2text(self.html).strip()
        """
        2. Content based data using regex
        In this case, we fallback to the raw text, and try to identify a pattern from a list of compiled Regex
        The compiled regex comes from:
        - https://github.com/mailgun/talon/blob/master/talon/quotations.py
        - https://github.com/crisp-oss/email-reply-parser/blob/master/lib/regex.js
        """
        parsed_text = None
        for pattern in patterns:
            match = pattern.search(self.text)
            if match:
                parsed_text = match.group(0)
                break

        if not parsed_text:
            self.no_patterns_found(self.text)
            return False

        self.text = self.text[0:self.text.find(parsed_text)].strip()

        if self.html:
            # Ok, now we have the text, we need to find a where it is present in the html to remove the next things
            # If we can't find it, we will rebuild the html from the text using markdown

            # loop over the soup object and build the string of content as we go until we find the parsed_text
            # then we will remove everything after that
            content = ''

            matching_tag = None
            lookup_text = self._clear_text(parsed_text)
            for tag in soup.descendants:
                if not isinstance(tag, NavigableString):
                    continue

                current_text = str(tag)
                if not current_text:
                    continue

                content += self._clear_text(current_text)

                if content.find(lookup_text) > -1:
                    matching_tag = tag
                    break

            if matching_tag:
                # We remove everything after
                for item in matching_tag.find_all_next():
                    if not isinstance(item, NavigableString):
                        item.decompose()

                # We do the reverse now, we go up until we find the exact text.
                # If we do (find === 0), we remove entirely.
                # If we do find with find > 0, we remove the previous tag
                # Otherwise we do nothing

                previous_tag = matching_tag
                found = False
                while matching_tag:
                    content = str(matching_tag) if isinstance(matching_tag, NavigableString) else matching_tag.get_text()
                    content = self._clear_text(content)

                    find_index = content.find(lookup_text)

                    if find_index == 0:
                        # Exact match, we delete everything and it's parent
                        found = True
                        break
                    elif find_index > 0:
                        # Found, but with others, we delete the previous tag
                        matching_tag = previous_tag
                        found = True
                        break

                    previous_tag = matching_tag
                    matching_tag = matching_tag.parent

                if found:
                    # If parent has no text and no image, we remove them too:
                    parent = matching_tag.parent
                    matching_tag.decompose()
                    while parent:
                        if not parent.get_text(strip=True) and not parent.find_all('img'):
                            parent.decompose()
                            parent = parent.parent
                        else:
                            break

                self.html = str(soup).strip()
            else:
                # We rebuild the html from the text
                self.html = self.text_to_html(self.text)
                if self.html:
                    self.html = self.html.strip()

        return True

    def text_to_html(self, data):
        return markdown.markdown(
            data,
            extensions=['sane_lists', 'nl2br', 'fenced_code', 'codehilite', 'legacy_em'],
            output_format='html5'
        )

    def quote_found(self, data):
        return

    def sign_found(self, data):
        return

    def no_patterns_found(self, text):
        return
