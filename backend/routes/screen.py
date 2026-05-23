import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import httpx

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.database import get_db
from backend.models import FreeIPUsage, PaidOrder, Report, Submission

router = APIRouter()

REPORTS_DIR       = os.getenv("REPORTS_DIR", ".tmp/reports")
SHEETS_WEBHOOK    = os.getenv("GOOGLE_SHEETS_WEBHOOK_URL", "")

# ── Tier account limits ───────────────────────────────────────────────────────
TIER_ACCOUNT_LIMITS = {"free": 1, "standard": 3, "attorney": 10}

# ── Free-tier IP tracking is persisted in DB (FreeIPUsage table) ──────────────

# ── Disposable / temp-mail domain blocklist ───────────────────────────────────
DISPOSABLE_DOMAINS = {
    # Mailinator family
    "mailinator.com","mailinator.net","mailinator.org","mailinator2.com",
    "mailinater.com","maildrop.cc","mailnull.com","mailnesia.com",
    "mailfree.ga","mailfreeonline.com","mailmetrash.com","mailscrap.com",
    "mailsiphon.com","mailslite.com","mailtemp.info","mailtemporaire.fr",
    "mailzilla.com","mailzilla.org","mail-temporaire.fr","mail-temp.com",
    "mail.tm","mails.gq","mailcatch.com","mailbidon.com","mailbucket.org",
    "mailc.net","mailchop.com","mailcuk.com","mailexpire.com","mailf.com",
    "mailblocks.com","mailanalyzer.com","mailpick.biz","mailrock.biz",
    "mailseal.de","mailshell.com","mailshuttle.com","mailsifu.com",
    "mailzipp.com","maileater.com","mailimate.com","mailim.de",
    # GuerrillaMAil family
    "guerrillamail.com","guerrillamail.info","guerrillamail.biz",
    "guerrillamail.de","guerrillamail.net","guerrillamail.org",
    "guerrillamailblock.com","grr.la","sharklasers.com","guerillamail.com",
    "gustr.com","spam4.me",
    # 10minutemail family
    "10minutemail.com","10minutemail.net","10minutemail.org","10minutemail.de",
    "10minutemail.ru","10minutemail.be","10minutemail.cf","10minutemail.ga",
    "10minutemail.gq","10minutemail.ml","10minutemail.tk","10minemail.com",
    "10minut.com.pl","10minut.xyz","10minutenemail.de","tenminutemail.com",
    "minuteinbox.com","min.10minutemail.com","mt2015.com","mt2016.com",
    "mt2017.com","mt2014.com","mt2009.com","mxp.dns.ms","mt2014.com",
    # Tempmail family
    "tempmail.com","tempmail.net","tempmail.org","tempmail.de","tempmail.eu",
    "tempmail.it","tempmail.us","tempmail2.com","tempr.email","temp-mail.org",
    "temp-mail.ru","temp-mail.de","temp-mail.io","tempemail.biz",
    "tempemail.co.za","tempemail.com","tempemail.net","tempemail.us",
    "tempinbox.co.uk","tempinbox.com","tempomail.fr","temporarioemail.com.br",
    "temporaryemail.net","temporaryemail.us","temporaryforwarding.com",
    "temporaryinbox.com","temporarymail.gq","tempthe.net","tmail.com",
    "tmail.io","tmailinator.com","tmail.ws","tmpmail.net","tmpmail.org",
    "tmpjunk.com","trashmail.app","temp-mail.info","tempr.net",
    "tempsky.com","tempail.com","tempinbox.org","tempemail.info",
    # Throwaway / Trash family
    "throwaway.email","throwam.com","throwam.co","throwem.com",
    "trashmail.at","trashmail.io","trashmail.me","trashmail.net",
    "trashmail.com","trashmail.de","trashmail.org","trashmail.se",
    "trashmailer.com","trashymail.com","trashinbox.com","trashimail.com",
    "trashemail.de","trashdevil.com","trashdevil.de","trashmail.gq",
    "trashmail.xyz","trashmail2.com","trashemiail.de",
    # Yopmail family
    "yopmail.com","yopmail.fr","yopmail.net","yopmail.pp.ua",
    "cool.fr.nf","jetable.fr.nf","nospam.ze.tc","nomail.xl.cx",
    "mega.zik.dj","speed.1s.fr","courriel.fr.nf","moncourrier.fr.nf",
    "monemail.fr.nf","monmail.fr.nf","cool.fr.nf","jetable.fr.nf",
    # Discard / Disposable family
    "dispostable.com","discardmail.com","discard.email","discardmail.de",
    "discardmail.net","dispostable.net","dispostable.org",
    # SpamGourmet / SpamFree family
    "spamgourmet.com","spamgourmet.net","spamgourmet.org",
    "spamfree24.org","spamspot.com","spamfree.eu","spamavert.com",
    "spambob.com","spambob.net","spambob.org","spamcero.com",
    "spamday.com","spamdecoy.net","spamgoes.in","spamhole.com",
    "spamkill.info","spamlot.net","spamnot.com","spamoff.de",
    "spamslicer.com","spamstack.net","spamtroll.net","spamtrail.com",
    "spamevader.com","spamobox.com","spamex.com","spam.la",
    "spamherelots.com","spamhereplease.com","spamthisplease.com",
    "spambox.us","spam.su","spaminhere.com","spamcorptastic.com",
    # Fake / Burner mail
    "fakeinbox.com","fakeinbox.org","fakeinbox.net","fake-email.com",
    "fakeemailgenerator.com","bugmenot.com","burnmail.ca","burnermail.io",
    "burnermail.co","binkmail.com","binnig.de","bobmail.info",
    "chammy.info","devnullmail.com","dingbone.com","fudgerub.com",
    "lookugly.com","smellfear.com","uggsrock.com","thisisnotmyrealemail.com",
    "tradermail.info","nowmymail.net","notsharingmy.info",
    # EmailOnDeck and similar single-use
    "emailondeck.com","emailondeck.net","emailondeck.org",
    "filzmail.com","junk1.com","getairmail.com","getonemail.com",
    "inoutmail.de","inoutmail.eu","inoutmail.info","inoutmail.net",
    "mohmal.com","trbvm.com","mvrht.com","moakt.com","moakt.cc",
    "moakt.de","moakt.ws","mytemp.email","mynewemails.com",
    "mytrashmail.com","mytempemail.com","mt2016.com","mt2017.com",
    # Nada / Getnada
    "getnada.com","nada.email","nadamail.com","nada.ltd",
    # Guerrilla-adjacent and other popular ones
    "incognitomail.com","incognitomail.net","incognitomail.org",
    "hmamail.com","inboxbear.com","inboxdesign.me",
    "kasmail.com","keepmymail.com","killermail.com","letthemeatspam.com",
    "mailandftp.com","mailmetrash.com","migmail.net","mierdamail.com",
    "mintemail.com","netzidiot.de","nobulk.com","noclickemail.com",
    "noicd.com","nonspam.eu","objectmail.com","obobbo.com",
    "odaymail.com","oneoffmail.com","opayq.com","otherinbox.com",
    "pancakemail.com","pookmail.com","popletter.com","postacin.com",
    "punkass.com","put2.net","qwickmail.com","rcpt.at","recode.me",
    "safetymail.info","sandelf.de","shieldedmail.com","shiftmail.com",
    "skeefmail.com","slopsbox.com","smashmail.de","sofort-mail.de",
    "stinkefinger.net","sweetxxx.de","tafmail.com","tagyourself.com",
    "teleworm.us","teleworm.com","temporaryemail.info","tempinbox.com",
    "tilien.com","tittbit.in","toiea.com","topranklist.de",
    "trickmail.net","trillianpro.com","tryalert.com","turual.com",
    "twinmail.de","tyldd.com","umail.net","uroid.com",
    "valemail.net","veryrealemail.com","vidchart.com","viditag.com",
    "vipmail.name","vpn.st","walala.org","walkmail.net","webemail.me",
    "weg-werf-email.de","wegwerfadresse.de","wegwerfemail.com",
    "wegwerfemail.de","wegwerfemail.net","wegwerfemail.org","wegwerfmail.de",
    "wegwerfmail.info","wegwerfmail.net","wegwerfmail.org",
    "wilemail.com","willselfdestruct.com","winemaven.info","wmails.com",
    "wmail.cf","wolfsmail.de","wox.email","wtfhub.com","wuzupmail.net",
    "xemaps.com","xents.com","xmaily.com","xoxy.net","xsmail.com",
    "y6mail.com","yapped.net","yogamaven.com","yoru-dea.com",
    "yotrashi.com","zehnminuten.de","zehnminutenmail.de","zetmail.com",
    "zippymail.info","zoaxe.com","zoemail.com","zoemail.net",
    "zoemail.org","zomg.info","zooglemailsucks.com","zpeak.com",
    # 33mail, AnonAddy, etc. (forwarders commonly abused)
    "33mail.com","anonaddy.com","anonaddy.me","anonaddy.dk",
    "addy.io","aleeas.com","spamgourmet.com",
    # Cock.li and related edgy throwaway hosts
    "cock.li","cock.email","airmail.cc","gun.team","waifu.club",
    "getbackinthe.kitchen","national.shitposting.agency","rape.lol",
    "tfwno.gf","gook.team",
    # GuerrillaMail single-use subdomains format
    "spam4.me","grr.la","sharklasers.com","guerrillamail.info",
    # Misc widely-seen in abuse lists
    "emlpro.com","emltmp.com","emlhub.com","emkei.cz",
    "instantemailaddress.com","instamail.fr","instantbooze.com",
    "internet.com.yt","internet-e-mail.de","internet-email.de",
    "internet-zeit.de","ipsur.org","irc.so","irish2me.com",
    "jetable.com","jetable.org","jetable.net","jetable.pp.ua",
    "jnxjn.com","jourrapide.com","jsrsolutions.com","jugglepile.com",
    "jumonji.tk","kabissa.org","kademen.com","kamote.net",
    "klassmaster.com","klassmaster.net","klzlk.com","koszmail.pl",
    "kurzepost.de","laxo.net","lazyinbox.com","letmail.net",
    "lol.ovpn.to","lolnow.de","lolfreak.net","lovemeet.faith",
    "lr7.us","lr78.com","lroid.com","lukop.dk",
    "m4ilweb.info","mail-easy.fr","mail-fake.com","mail-generator.net",
    "mail-temporaire.com","mail2trash.com","mailboxy.fun",
    "mailcat.biz","mailda.net","mailfall.com","mailguard.me",
    "mailhazard.com","mailhazard.us","mailhex.com","mailimate.com",
    "mailismagic.com","mailkutu.com","maillnk.com","mailme.ir",
    "mailme.lv","mailme24.com","mailmight.com","mailmoat.com",
    "mailms.com","mailnew.com","mailnew.de","mailnowto.com",
    "mailorc.com","mailpokemon.com","mailproxsy.com","mailracer.com",
    "mailretreiver.com","mailsac.com","mailseal.de","mailsucker.net",
    "mailtm.com","mailts.com","mailtv.net","mailundo.com",
    "mailv.net","mailvery.com","mailvizo.com","mailw.info",
    "mailwithyou.com","mailwolf.de","manya.site","mbox.re",
    "mcache.net","mdinbox.com","mega-zik.de","messwiththebestdielikethe.rest",
    "memail.com","mfsa.ru","mgbmx.com","mhzayt.online",
    "mid.net","midnightclubs.com","mils.ru","mindblowermail.com",
    "mintemail.com","misterpinball.de","mjukglass.nu","mkp224o.eu",
    "mmail.igg.biz","mnetservices.com","mogadishu.com","mohmal.in",
    "momentics.ru","money.net","moonfang.us","moreorless.at",
    "mox.pp.ua","msgweb.eu","mswork.ru","mt2015.com",
    "mucincanon.com","muchmail.com","mudo.pl","munouburo.com",
    "mvrht.net","myalias.pw","mymacmail.com","myopera.com",
    "myspaceinc.com","myspaceinc.net","myspaceinc.org",
    "nbox.notif.me","nexus.ug","nic.in","noclickemail.com",
    "nogmailspam.info","nomail.pw","nomail2me.com","nospamfor.us",
    "nospamthanks.info","notmailinator.com","nowmymail.com",
    "nwldx.com","nwytg.com","nwytg.net","nwytg.org",
    "obobbo.com","odmail.com","oe.oe.pl","officedomain.com",
    "ohaaa.de","ohno.de","okrent.us","okzk.com",
    "olimp.olsztyn.pl","omnievents.org","onewaymail.com",
    "onlatedotcom.info","onlineidea.info","onlinemail.xyz",
    "onqin.com","oonies.com","open.tc","openforum.eu",
    "ora21.it","oracleservers.com","orehova-gora.si","orlandonaturalhealth.com",
    "otonmail.ga","ourklips.com","outlawspam.com","ovvee.com",
    "owlpic.com","paplease.com","peew.ru","pepbot.com",
    "pimpedupmyspace.com","pinnweblog.info","pjjkp.com",
    "plexolan.de","pm.com","pokemail.net","politikerclub.de",
    "poolsport.info","postbot.com","postinbox.com","ppetw.com",
    "privacy.net","proxymail.eu","prtnx.com","prtz.eu",
    "qq.com.de","qsl.ro","quackquack.dk","quickinbox.com",
    "rabbbits.com","radical-zone.nl","ranmamail.com","raqid.com",
    "ratafia.de","razormail.se","realemail.net","recursor.net",
    "regbypass.com","rejectmail.com","reloadevery.com","rfgmail.de",
    "rklips.com","rkomo.com","rku.us","rlhyfqj.com",
    "rmqkr.net","rn.com","roewe.gmbh","rohingya.org",
    "rollindo.agency","rolls-royce-motor-cars-na.com","rpifan.info",
    "rppkn.com","rsvhr.com","rtskiya.xyz","ruby-lang.org.uk",
    "ruffrey.com","runa.ml","runbox.com.de","rupayamail.com",
    "rustydagger.com","ruugafuu.com","rvb.ro","rxan.de",
    "s0ny.net","safetypost.de","safermail.info","sanam.net",
    "sanstr.com","sapo.de","sendfree.org","sendspamhere.com",
    "sharewaredevelopers.com","shed.de","sheila.nom.za",
    "shhmail.com","shiphazmat.org","shoklin.de","shortmail.net",
    "shotmail.ru","showslow.de","shrib.com","shurs.xyz",
    "shutupandtakemyshteam.com","sibmail.com","simpleitsecurity.info",
    "siriusclear.com","skeefmail.com","skurgemails.com","slaskpost.se",
    "slopsbox.com","smail.com","smailpro.com","snakemail.com",
    "sneakemail.com","snkmail.com","sofimail.com",
    "sofort-mail.de","sogetthis.com","spam.netpirates.net",
    "spam.org.es","spamcon.org","spamdo.com","spamfree24.de",
    "spamfree24.eu","spamfree24.info","spamfree24.net","spamfree24.org",
    "spaminator.de","spamkitchen.com","spamoff.de","spamomatic.com",
    "spamthis.co.uk","speedymail.org","sq.le.vu","sr.de",
    "ssoia.com","startpage.com.de","steht.org","stinkefinger.net",
    "stop-my-spam.pp.ua","streamfly.biz","stuffmail.de",
    "suburbanthug.com","sunder.email","sunmail.cf","sunmail.ga",
    "sunmail.gq","sunmail.ml","sunmail.tk","super-auswahl.de",
    "supergreatmail.com","supermailer.jp","suremail.info","svk.jp",
    "sweetxxx.de","syosetu.com","tafmail.com","tagyourself.com",
    "takuyakimura.tk","tanukis.org","tao-te.uk","taxi.de",
    "tcwlm.com","techemail.com","teerest.com","telfort.nl",
    "telfort.nl.de","teleworm.com","teleworm.us",
    "tempalias.com","tempe-mail.com","tempinbox.co.uk",
    "temporaryemail.info","tempr.biz","tempr.de","tempr.info",
    "tempr.net","tempr.org","tempr.xyz","tempsky.com",
    "thecloudindex.com","thetimestamp.com","thinktom.info",
    "thundermail.de","tidni.com","timnow.com","tinoza.org",
    "tinyurl24.com","tiv.cc","tmail.com.br","tmail.io","tmail1.com",
    "toiea.com","toomail.biz","topranklist.de","trabiu.net",
    "trayna.com","trbvm.net","trickmail.net","trillianpro.com",
    "troubledmailbox.com","tryalert.com","ttirv.net","turual.com",
    "twitpost.info","tyldd.com","ubm.md","ubunu.com",
    "uggsrock.com","umail.net","uroid.com","utemail.net",
    "utimail.com","valemail.net","vctel.com","velocriminal.com",
    "venompen.com","veryrealemail.com","viditag.com","viewcastmedia.com",
    "vipmail.name","vipmail.pw","vkcode.ru","vpn.st",
    "vtxmail.us","vubby.com","walala.org","walkmail.net",
    "watchfull.net","weg-werf-email.de","wegwerfadresse.de",
    "wegwerfemail.com","wegwerfemail.de","wegwerfemail.net",
    "wegwerfemail.org","wegwerfemails.de","wegwerfmail.de",
    "wegwerfmail.info","wegwerfmail.net","wegwerfmail.org",
    "wegwerfmails.de","wh4f.org","whatiaas.com","whatpaas.com",
    "whatsaas.com","whopy.com","wilemail.com","willhackforfood.biz",
    "willselfdestruct.com","winemaven.info","wmails.com","wmail.cf",
    "wolfsmail.com","wolfsmail.de","worldspace.link","wox.email",
    "wtfhub.com","wuzupmail.net","xemaps.com","xents.com",
    "xmaily.com","xn--9kq967o.com","xoxy.net","xpectationstoo.com",
    "xsmail.com","xzapmail.com","y6mail.com","yapped.net",
    "yep.it","yogamaven.com","yoru-dea.com","yotrashi.com",
    "ypmail.webarnak.fr.eu.org","yuurok.com","z1p.biz","zehnminuten.de",
    "zehnminutenmail.de","zetmail.com","zippymail.info","zoaxe.com",
    "zoemail.com","zoemail.net","zoemail.org","zomg.info",
    "zooglemailsucks.com","zopzop.com","zpeak.com",
    # Newer / popular as of 2024-2025
    "tempmail.lol","tempmail.plus","tempmail.ninja","tempmail.gg",
    "tempmail.social","disposablemail.com","disposablemail.net",
    "dropmail.me","cryptogmail.com","getnotify.com","emailfake.com",
    "emailfake.icu","emailsecure.ru","emailondeck.net","emailondeck.org",
    "emailfree.ga","email-temp.com","email-jetable.fr","emailtemporaire.fr",
    "emailtemporar.ro","emailtemporany.com","emailto.de","emailtmp.com",
    "emailz.cf","emailz.ga","emailz.gq","emailz.ml","emailz.tk",
    "etempmail.com","easytrashmail.com","e4ward.com","ez.lv",
    "fakemailz.com","fakemail.fr","fakemail.net","fakemail.org",
    "fakemail.us","fakemails.ga","fakemails.net","faketempmail.com",
    "fastacura.com","fastcars.com","fastchevy.com","fastchrysler.com",
    "fastnissan.com","fastsubaru.com","fasttoyota.com","fastzx.com",
    "filbert8.com","fleckens.hu","fly-ts.de","flurred.com",
    "flyspam.com","fmailbox.com","fmailc.com","forgetmail.com",
    "fightallspam.com","filzmail.de","garbageemail.org","gardenscape.ca",
    "garizo.com","gavtelecom.ru","gawab.com","gehensieanscheisskopf.de",
    "gelitik.in","geschent.biz","get1mail.com","get2mail.fr",
    "getlink.pw","getmails.eu","getnowdeal.com","getts.eu",
    "gigamailz.com","gilderbloom.com","gishpuppy.com","girlmail.net",
    "glitch.sx","goemailgo.com","gotmail.net","gotmail.org",
    "grandmamail.com","grandmasmail.com","greencafe24.com",
    "greensloth.com","greenmail.xyz","grish.de","groupmail.com",
    "grr.la","gsrv.co.uk","gteborg.com","gustr.com","gusto.at",
    "guvewi.gq","h8s.org","hacccc.com","haltospam.com",
    "hatespam.org","harakirimail.com","herp.in","hidemail.de",
    "hidzz.com","hiyrey.ml","hlzwu.com","hmamail.com",
    "hn.com","hochsitze.com","hookmail.net","hopemail.biz",
    "hortulan.com","host-info.com","hotpop.com","hp.com.de",
    "hsource.com","hulababy.com","humanoid.net","hurify1.com",
    "hvuskhqrp.xyz","hype-machine.com","hyper.com",
    "ieatspam.eu","ieatspam.info","ieh-mail.de","ihateyoualot.info",
    "iheartspam.org","ikbenspamvrij.nl","illistnoise.com",
    "imail.org","imgof.com","immo-gerance.info","imovies.com",
    "inbound.plus","incognitomail.com","inetdoor.com",
    "info.com.de","info.net.de","info.pl","infogroup.com",
    "insidebeltway.com","internet.com.yt","ipoo.org","ipoormail.com",
    "ipsur.org","irc.so","iroid.com","iwi.net",
    "jetable.com","jetable.net","jetable.org","jetable.pp.ua",
    "jnxjn.com","jourrapide.com","jsrsolutions.com","jumonji.tk",
    "kasmail.com","kaspop.com","katamail.com","kazahel.com",
    "keep-a-secret.at","keepmymail.com","kemptvillebaseball.com",
    "kingsq.ga","klassmaster.com","klassmaster.net","klzlk.com",
    "koszmail.pl","kurzepost.de","laxo.net","lazyinbox.com",
    "letmail.net","lol.ovpn.to","lolfreak.net","lolnow.de",
    "lovemeet.faith","lr7.us","lr78.com","lroid.com",
    "lukop.dk","m4ilweb.info","maildax.com","mailboxy.fun",
    "mailca.com","maild.pro","maildu.de","mailey.pw",
    "mailfree.ga","mailguard.me","mailhazard.com","mailhazard.us",
    "mailhex.com","mailimate.com","mailismagic.com","mailkutu.com",
    "maillnk.com","mailme.ir","mailme.lv","mailme24.com",
    "mailmight.com","mailmoat.com","mailms.com","mailnew.com",
    "mailnew.de","mailnowto.com","mailorc.com","mailproxsy.com",
    "mailracer.com","mailsac.com","mailsucker.net","mailtm.com",
    "mailts.com","mailtv.net","mailundo.com","mailv.net",
    "mailvery.com","mailvizo.com","mailw.info","mailwithyou.com",
    "mailwolf.de","manya.site","mbox.re","mcache.net",
    "mdinbox.com","mfsa.ru","mgbmx.com","mid.net",
    "mindblowermail.com","mintemail.com","misterpinball.de",
    "mjukglass.nu","mmail.igg.biz","mnetservices.com","mohmal.in",
    "momentics.ru","moonfang.us","mox.pp.ua","msgweb.eu",
    "mswork.ru","mucincanon.com","muchmail.com","mudo.pl",
    "munouburo.com","mvrht.net","myalias.pw","mymacmail.com",
    "nbox.notif.me","nexus.ug","nogmailspam.info","nomail.pw",
    "nomail2me.com","nospamfor.us","nospamthanks.info",
    "notmailinator.com","nowmymail.com","nwldx.com","nwytg.com",
    "nwytg.net","nwytg.org","ohaaa.de","ohno.de",
    "okrent.us","okzk.com","onewaymail.com","onlatedotcom.info",
    "onlinemail.xyz","onqin.com","ora21.it","otonmail.ga",
    "peew.ru","pepbot.com","plexolan.de","pokemail.net",
    "politikerclub.de","ppetw.com","prtnx.com","prtz.eu",
    "quickinbox.com","rabbbits.com","ranmamail.com","raqid.com",
    "ratafia.de","rejectmail.com","rfgmail.de","rklips.com",
    "rkomo.com","rku.us","rmqkr.net","rppkn.com",
    "rsvhr.com","ruby-lang.org.uk","ruffrey.com","runbox.com.de",
    "rupayamail.com","rustydagger.com","safermail.info","sanam.net",
    "sanstr.com","sendfree.org","sendspamhere.com","shhmail.com",
    "shotmail.ru","showslow.de","shrib.com","sibmail.com",
    "simpleitsecurity.info","siriusclear.com","skurgemails.com",
    "slaskpost.se","smailpro.com","sneakemail.com","snkmail.com",
    "sofimail.com","sogetthis.com","speedymail.org","ssoia.com",
    "startpage.com.de","streamfly.biz","stuffmail.de",
    "suburbanthug.com","sunder.email","sunmail.cf","sunmail.ga",
    "sunmail.gq","sunmail.ml","sunmail.tk","super-auswahl.de",
    "supergreatmail.com","supermailer.jp","svk.jp","sweetxxx.de",
    "sunder.email","stop-my-spam.pp.ua","sq.le.vu",
    # Additional 2024+ burner domains
    "dismail.de","disposableinbox.com","disposablemail.is",
    "dropmail.me","dsten.de","duck.com",
    "echomail.app","emas.xyz","emkei.ga","emlhub.com",
    "emlpro.com","emltmp.com","enayu.com","etempmail.com",
    "exifn.com","easytrashmail.com","fakedemail.com",
    "fakeemail.com","fakeemail.net","fakeemails.com",
    "fake-mail.net","fakemailgenerator.net","fakemail.xyz",
    "fightallspam.com","freemail.net","freeomailbox.com",
    "freshmail.top","friendlymail.co.uk","frwrd.email",
    "fuckingduh.com","fumets.com","fux0ringduh.com",
    "garbagemail.org","getairmail.cf","getairmail.ga",
    "getairmail.gq","getairmail.ml","getairmail.tk",
    "getonemail.net","getonemail.org","girlsundertheinfluence.com",
    "gmailbox.net","gmaill.com","gmx.com.de","goemailgo.com",
    "gotmail.com","great-host.in","grr.la",
    "guycreations.com","ifw.io","inboxalias.com",
    "incagames.com","indomail.club","inoutmail.com",
    "instantbooze.com","instantemailaddress.com",
    "jumonji.tk","kasmail.net","keepmymail.net","letmemail.com",
    "loblaw.ca.de","lowcost.com.de","lt9.com",
    "lunchmail.de","lyricspad.net","mail-filter.com",
    "mail-address.bid","mailandftp.com","mailbox52.ga",
    "mailbox72.biz","mailbox80.biz","mailbox87.ga",
    "mailbox92.biz","mailboxfree.com","mailboxprotector.com",
    "mailboxy.fun","mailchi.mp.de","mailck.com",
    "mailconsult.de","mailcontact.com","mailcorvette.com",
    "mailcu.com","maildx.com","maile.lol","mailenew.com",
    "mailerino.com","maileru.com","mailfull.com","mailgov.co",
    "mailguard.net","mailhol.com","mailhound.club",
    "mailhz.me","mailimate.net","mailin8r.com","mailinator.gq",
    "mailinator.info","mailinator.net","mailinator.org",
    "mailismagic.net","mailivery.com","mailkeyboard.com",
    "mailnesia.net","mailnesia.org","mailnew.eu","mailnuke.com",
    "mailorc.net","mailox.biz","mailox.fun","mailparayas.com",
    "mailpokemon.net","mailproxsy.net","mailquack.com",
    "mailranker.com","mailrelief.com","mailrip.com",
    "mailrock.biz","mailrure.com","mailsand.com",
    "mailseal.net","mailservice1.de","mailsex.net","mailsimply.com",
    "mailslapping.com","mailslite.net","mailsparks.com",
    "mailsph.com","mailsucker.de","mailtechx.com","mailtemp.net",
    "mailtemporaire.com","mailtemporaire.net","mailterrain.com",
    "mailtocoupons.com","mailtonews.com","mailtotrash.com",
    "mailtv.tv","mailuc.com","mailue.com","mailup.net",
    "mailur.de","mailvault.com","mailvedant.com","mailw.de",
    "mailwall.de","mailwithme.net","mailworks.org","mailwrite.com",
    "mailwww.com","mails.vin","mails.zone","mails.solutions",
    "mailtome.de","mailtra.de","malboxe.com","megarobo.com",
    "meltmail.com","mfsa.info","mh0.net","mhzayt.com",
    "microbox.de","mirroredmail.com","miur.de","mixmail.com",
    "mlt.de","mobi.de","mobileninja.co.uk","moburl.com",
    "moeri.org","mofkac.de","mohmal.com","mohmal.net",
    "mohmal.org","mol2b.com","monopgm.com","mosquitomail.com",
    "my10minutemail.com","my0.co","mydefshield.com",
    "mygamingmail.com","mymail-in.net","mymail90.com",
    "mymailoasis.com","mymails.top","mynetstore.de","myopera.com",
    "mypartyclip.de","myprivatemail.net","myspaceinc.com",
    "myspaceinc.net","myspaceinc.org","mytemporarymails.com",
    "mytmpmail.com","nadas.io","nana.no","nanonym.gq",
    "napalm51.com","nasz.pl","nbox.notif.me","ne.no",
    "neomails.com","nerdmail.co","newmail.top","nicebush.com",
    "nicetry.info","nikotin.dk","ninjamail.com","ninemails.com",
    "niqmail.com","nmail.cf","nomail.ga","noclickemail.net",
    "noref.in","norseforce.com","nothingtoseehere.ca","nowmymail.org",
    "nudepic.xyz","null.net","nullbox.info","numbersmail.com",
    "o.pe.je","o2.pl.de","obobbo.net","odmail.net",
    "odmail.org","odrmail.com","oe.oe.de","of.tc",
    "officedomain.net","officedomain.org","ohno.net",
    "omegafear.com","omail.pro","onestopmail.com","oogit.com",
    "opentrash.com","orcs.de","orgmail.net","oscr.de",
    "our.com.de","ourklips.net","ovvee.net","owlpic.net",
    "palepeo.com","panotube.com","papierkorb.me","parkmail.xyz",
    "passoutemails.com","payperex2.com","pepbot.net",
    "pfui.ru","pigeonportal.com","pimpedupmyspace.net",
    "pjjkp.net","planet.dk","planningacrime.com",
    "playersodds.com","pleasenomore.com","plexolan.net",
    "pluno.biz","pointlogics.com","politikerclub.net",
    "postale.io","postinbox.net","postpro.net","privacy.com.de",
    "proxymail.eu","prtnx.net","prtz.net","publicmail.net",
    "put2.de","qsl.de","qsmfuck.com","quackquack.me",
    "quickinbox.net","ra3.us","rabbbits.net","radical-zone.de",
    "ranmamail.net","raqid.net","ratafia.net","rcpt.net",
    "realemail.de","recursor.de","regbypass.net","rejectmail.net",
    "reloadevery.net","rfgmail.net","rklips.net","rkomo.net",
    "rku.net","rlhyfqj.net","rmqkr.com","roewe.net",
    "rohingya.net","rollindo.net","rolls-royce.net.de",
    "rpifan.net","rppkn.net","rsvhr.net","rtskiya.net",
    "runbox.de","rupayamail.net","rustydagger.net","ruvix.ru",
    "s0ny.biz","sanam.biz","sanstr.net","sapo.net",
    "sed.mx","segone.com","selfdestructingmail.com",
    "selfdestructingmail.org","sendingspecialflyers.com",
    "senseless-entertainment.com","sevgendur.com",
    "sfamo.com","sharedmailbox.org","sharklasers.net",
    "shed.net","shhmail.net","shiphazmat.net","shopregion.de",
    "shrib.net","sibmail.net","sify.net.de",
    "simpleitsecurity.net","skim.com","skurgemails.net",
    "slashmail.me","sletmail.com","slopsbox.net",
    "smail.net","smailpro.net","snakemail.net","sneakemail.net",
    "snkmail.net","sofimail.net","sofort-mail.net",
    "sogetthis.net","somail.xyz","spam.care","spam.dk",
    "spam.la","spam.lycos.com","spam.net","spam.nl",
    "spam.netpirates.net","spam.org.es","spam.pe",
    "spam.piber.com","spam.su","spam.wf","spambin.com",
    "spambox.info","spambox.irishspringrealty.com","spambox.me",
    "spambox.win","spamcon.net","spamcon.org","spamcop.net",
    "spamdo.net","spamfighter.net","spamfree24.de",
    "spamfree24.eu","spamfree24.info","spamfree24.net",
    "spamgoes.net","spamhole.net","spamify.net","spaminator.net",
    "spamjob.com","spamkitchen.net","spaml.de","spammotel.com",
    "spammy.de","spamobox.net","spamomatic.net","spamotron.com",
    "spampocalypse.com","spampurge.com","spamrecycle.com",
    "spamslicer.net","spamspot.net","spamstack.com","spamtoll.com",
    "spamtrap.ro","spamtroll.com","spamtrail.net","spamville.net",
    "speedymail.net","squizzy.de","squizzy.net","ssoia.net",
    "statdvr.com","stealthmail.com","stop-my-spam.net",
    "streamfly.net","stuffmail.net","suburbanthug.net","sunder.net",
    "sunnet.biz","super-auswahl.net","supergreatmail.net",
    "supermailer.net","suremail.net","svk.net","sweetxxx.net",
    "tafmail.net","tagyourself.net","takingyoudown.com",
    "tanukis.net","taxi.net","techemail.net","teerest.net",
    "telfort.net","temporaryemails.com","temporaryforwarder.com",
    "temporaryinbox.net","tempr.net","tempsky.net",
    "thankyou2010.net","thanksnospam.net","thecloudindex.net",
    "thetimestamp.net","thinktom.net","thundermail.net",
    "tidni.net","timnow.net","tinoza.net","tinyurl24.net",
    "tiv.net","tmailbox.net","toomail.net","topranklist.net",
    "trabiu.com","trayna.net","trbvm.com","trillianpro.net",
    "tryalert.net","ttirv.com","twinmail.net","tyldd.net",
    "ubm.net","umail.biz","uroid.net","utemail.biz",
    "utimail.net","valemail.biz","vctel.net","velocriminal.net",
    "venompen.net","veryrealemail.net","vidchart.net",
    "viditag.net","vipmail.biz","vkcode.net",
    "vubby.net","walala.net","walkmail.biz","watchfull.net",
    "webemail.net","wh4f.net","whatiaas.net","whatpaas.net",
    "whatsaas.net","whopy.net","wilemail.net",
    "willhackforfood.net","willselfdestruct.net",
    "winemaven.net","wmails.net","wolfsmail.net",
    "worldspace.net","wox.net","wtfhub.net","wuzupmail.biz",
    "xemaps.net","xents.net","xmaily.net","xoxy.biz",
    "xsmail.net","xzapmail.net","y6mail.net","yapped.biz",
    "yogamaven.net","yoru-dea.net","yotrashi.net",
    "zehnminuten.net","zetmail.net","zippymail.net",
    "zoaxe.net","zoemail.biz","zomg.net","zpeak.net",
}

def _get_client_ip(request: Request) -> str:
    fwd = request.headers.get("X-Forwarded-For")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
PROJECT_ROOT   = str(Path(__file__).resolve().parents[2])
MAX_ACCOUNTS   = 10
SCRAPE_TIMEOUT = 420  # 7 min — must be > APIFY_TIMEOUT (300s) + startup overhead
PROFILE_IMGS_DIR  = ".tmp/profile_images"
SCREENSHOTS_DIR   = ".tmp/screenshots"
# Playwright is installed in the Railway Docker image — screenshots enabled by default.
# Set ENABLE_SCREENSHOTS=false to disable if you see Chromium issues.
SCREENSHOTS_ENABLED = os.getenv("ENABLE_SCREENSHOTS", "true").lower() == "true"

# Platform handle → unavatar.io slug
_UNAVATAR_SLUG = {
    "twitter": "twitter", "x": "twitter",
    "instagram": "instagram",
    "tiktok": "tiktok",
    "youtube": "youtube",
    "facebook": "facebook",
}


def _fetch_profile_image_sync(platform: str, handle: str, report_id: str, idx: int) -> str:
    """Download profile avatar via unavatar.io. Returns local file path or ''."""
    slug = _UNAVATAR_SLUG.get(platform.lower(), "")
    if not slug:
        return ""
    clean = handle.lstrip("@").split("?")[0].rstrip("/").split("/")[-1]
    if not clean:
        return ""
    try:
        Path(PROFILE_IMGS_DIR).mkdir(parents=True, exist_ok=True)
        url = f"https://unavatar.io/{slug}/{clean}"
        r = httpx.get(url, timeout=8, follow_redirects=True)
        if r.status_code == 200 and len(r.content) > 500:
            ext = ".jpg"
            out = Path(PROFILE_IMGS_DIR) / f"{report_id}_{idx}{ext}"
            out.write_bytes(r.content)
            return str(out)
    except Exception:
        pass
    return ""


def _capture_screenshots_sync(flagged_posts: list, report_id: str) -> dict:
    """Screenshot each flagged post URL using Playwright. Returns {url: local_path}."""
    posts_with_url = [fp for fp in flagged_posts if (fp.get("post_url") or "").startswith("http")][:5]
    if not posts_with_url:
        return {}
    shots: dict = {}
    try:
        from playwright.sync_api import sync_playwright
        Path(SCREENSHOTS_DIR).mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(
                viewport={"width": 640, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            for i, fp in enumerate(posts_with_url):
                url = fp["post_url"]
                try:
                    page = ctx.new_page()
                    page.goto(url, wait_until="domcontentloaded", timeout=12000)
                    page.wait_for_timeout(2500)
                    out = str(Path(SCREENSHOTS_DIR) / f"{report_id}_{i}.png")
                    page.screenshot(path=out, full_page=False, clip={"x": 0, "y": 0, "width": 640, "height": 700})
                    page.close()
                    shots[url] = out
                except Exception:
                    pass
            browser.close()
    except Exception:
        pass
    return shots


# ── Schemas ───────────────────────────────────────────────────────────────────

class AccountInput(BaseModel):
    platform: str
    handle: str
    manual_posts: Optional[str] = None

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v):
        allowed = {"twitter", "x", "instagram", "tiktok", "linkedin", "facebook", "youtube"}
        if v.lower() not in allowed:
            raise ValueError(f"Platform must be one of: {', '.join(sorted(allowed))}")
        return v.lower()


class ScreeningRequest(BaseModel):
    name: str
    email: str
    country: str
    accounts: List[AccountInput]
    reason: str
    timeline: str
    consent: bool
    tier: str = "free"

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v):
        if v not in TIER_ACCOUNT_LIMITS:
            return "free"
        return v

    @field_validator("accounts")
    @classmethod
    def validate_accounts(cls, v):
        if not v:
            raise ValueError("At least one social media account is required.")
        if len(v) > MAX_ACCOUNTS:
            raise ValueError(f"Maximum {MAX_ACCOUNTS} accounts allowed per submission.")
        return v

    @field_validator("consent")
    @classmethod
    def must_consent(cls, v):
        if not v:
            raise ValueError("You must authorize screening to proceed.")
        return v


# ── Subprocess scraper ────────────────────────────────────────────────────────

def _run_scraper_sync(platform: str, handle: str) -> list[dict]:
    """Blocking subprocess call — run via executor so the event loop stays free."""
    script = str(Path(PROJECT_ROOT) / "tools" / "scrape_public_profile.py")
    try:
        result = subprocess.run(
            [sys.executable, script, platform, handle],
            capture_output=True,
            cwd=PROJECT_ROOT,
            timeout=SCRAPE_TIMEOUT,
        )
        err_text = result.stderr.decode("utf-8", errors="replace")
        if result.returncode != 0 or not result.stdout.strip():
            return [{"platform": platform,
                     "post_text": f"[SCRAPE_ERROR rc={result.returncode}: {err_text[:400]}]",
                     "post_url": "", "posted_at": None}]
        return json.loads(result.stdout.decode("utf-8", errors="replace"))
    except subprocess.TimeoutExpired:
        return [{"platform": platform, "post_text": "[SCRAPE_ERROR: timeout]",
                 "post_url": "", "posted_at": None}]
    except Exception as e:
        return [{"platform": platform, "post_text": f"[SCRAPE_ERROR: {e}]",
                 "post_url": "", "posted_at": None}]


async def scrape_account_subprocess(platform: str, handle: str) -> list[dict]:
    """Run scraper in a thread pool executor (avoids asyncio subprocess issues on Windows)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_scraper_sync, platform, handle)


# ── Manual post parser ────────────────────────────────────────────────────────

def parse_manual_posts(platform: str, raw: str) -> list[dict]:
    """Split pasted text into individual post dicts for AI analysis."""
    # Split on blank lines first; fall back to single-line splits
    blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
    if len(blocks) == 1:
        blocks = [b.strip() for b in raw.splitlines() if b.strip()]
    return [
        {"platform": platform, "post_text": block, "post_url": "", "posted_at": None}
        for block in blocks[:50]  # cap at 50
    ]


# ── Background job ────────────────────────────────────────────────────────────

async def run_screening_job(report_id: str, submission_data: dict):
    from backend.database import AsyncSessionLocal
    from tools.analyze_with_ai import analyze_posts
    from tools.generate_pdf import generate_pdf

    async with AsyncSessionLocal() as db:
        report = await db.get(Report, report_id)
        if not report:
            return

        report.status = "processing"
        report.updated_at = datetime.utcnow()
        await db.commit()

        try:
            accounts = submission_data.get("accounts", [])

            # 1. Collect posts — use pasted text when provided, else scrape
            all_posts: list[dict] = []
            for acc in accounts:
                platform = acc.get("platform", "twitter")
                manual = acc.get("manual_posts", "")
                if manual and manual.strip():
                    posts = parse_manual_posts(platform, manual.strip())
                else:
                    posts = await scrape_account_subprocess(platform, acc.get("handle", ""))
                all_posts.extend(posts)

            # 2. AI analysis (blocking — run in thread pool, 4-min hard cap)
            loop = asyncio.get_event_loop()
            analysis = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    analyze_posts,
                    all_posts,
                    submission_data["name"],
                    submission_data["country"],
                    submission_data["reason"],
                ),
                timeout=240.0,
            )

            # Enrich with submission metadata for PDF
            analysis["name"]     = submission_data["name"]
            analysis["email"]    = submission_data.get("email", "")
            analysis["country"]  = submission_data["country"]
            analysis["reason"]   = submission_data["reason"]
            analysis["timeline"] = submission_data.get("timeline", "")
            analysis["accounts"] = accounts

            # 3a. Fetch profile images for each account (non-blocking failures ignored)
            enriched_accounts = []
            for idx, acc in enumerate(accounts):
                img_path = await loop.run_in_executor(
                    None, _fetch_profile_image_sync,
                    acc.get("platform", ""), acc.get("handle", ""), report_id, idx,
                )
                enriched_accounts.append({**acc, "profile_image": img_path})
            analysis["accounts"] = enriched_accounts

            # 3b. Backfill post_url on flagged posts by text-matching against original scraped posts
            for fp in analysis.get("flagged_posts", []):
                if (fp.get("post_url") or "").startswith("http"):
                    continue
                fp_text = (fp.get("text") or "").strip().lower()[:150]
                if not fp_text:
                    continue
                for orig in all_posts:
                    orig_text = (orig.get("post_text") or "").strip().lower()
                    url = (orig.get("post_url") or "")
                    if not url.startswith("http"):
                        continue
                    if fp_text in orig_text or orig_text[:150] in fp_text:
                        fp["post_url"] = url
                        break

            # 3c. Screenshots — only if explicitly enabled (Playwright hangs on Railway)
            flagged = analysis.get("flagged_posts", [])
            if flagged and SCREENSHOTS_ENABLED:
                try:
                    screenshots = await asyncio.wait_for(
                        loop.run_in_executor(None, _capture_screenshots_sync, flagged, report_id),
                        timeout=25.0,
                    )
                except Exception:
                    screenshots = {}
                for fp in flagged:
                    url = fp.get("post_url", "")
                    if url and url in screenshots:
                        fp["screenshot_path"] = screenshots[url]

            # 4. Generate PDF (blocking — run in thread pool, 60-sec cap)
            Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
            pdf_path = f"{REPORTS_DIR}/{report_id}.pdf"
            await asyncio.wait_for(
                loop.run_in_executor(None, generate_pdf, analysis, pdf_path),
                timeout=60.0,
            )

            report.status      = "done"
            report.report_json = analysis
            report.pdf_path    = pdf_path

            # Mark submission as scan complete in Supabase
            try:
                from backend.models import Submission as Sub
                sub_row = await db.get(Sub, report.submission_id)
                if sub_row and sub_row.lead_status == "new":
                    sub_row.lead_status = "scan_done"
                    await db.commit()
            except Exception:
                pass

            # 5. Send "report ready" email
            user_email = submission_data.get("email", "")
            if user_email:
                try:
                    from backend.email_utils import send_email, report_ready_html
                    frontend_url = os.getenv("FRONTEND_URL", "https://visafootprint.com").rstrip("/")
                    report_url   = f"{frontend_url}/result/{report_id}"
                    risk_level   = analysis.get("overall_risk", "LOW").upper()
                    score        = int(analysis.get("risk_score", 0))
                    await send_email(
                        to=user_email,
                        subject="VisaFootprint — your report is ready",
                        html=report_ready_html(submission_data.get("name", ""), report_url, risk_level, score),
                    )
                except Exception as mail_err:
                    print(f"[EMAIL] report-ready send failed: {mail_err}", flush=True)

        except Exception as exc:
            import traceback
            tb = traceback.format_exc()
            print(f"[SCREENING ERROR] job={report_id}\n{tb}", flush=True)
            report.status        = "failed"
            report.error_message = tb[:3000]

        report.updated_at = datetime.utcnow()
        await db.commit()


# ── Google Sheets lead logger (fire-and-forget) ───────────────────────────────

async def _log_lead_to_sheets(payload: dict):
    if not SHEETS_WEBHOOK:
        return
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            await client.post(SHEETS_WEBHOOK, json=payload)
    except Exception:
        pass  # never block the screening flow


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/screen")
async def submit_screening(
    req: ScreeningRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    client_ip = _get_client_ip(request)

    # Block disposable / temp-mail addresses
    email_domain = req.email.lower().split("@")[-1] if "@" in req.email else ""
    if email_domain in DISPOSABLE_DOMAINS:
        raise HTTPException(
            status_code=400,
            detail="Disposable or temporary email addresses are not allowed. Please use a real email.",
        )

    is_free = req.tier == "free"

    _UPGRADE_MSG = "UPGRADE_REQUIRED: You've used your free scan. Upgrade to Standard ($49), Attorney-Reviewed ($199), or Monitor ($19/mo) to continue."

    if is_free:
        # Block by IP (lifetime, persisted in DB)
        ip_used = await db.execute(
            select(FreeIPUsage).where(FreeIPUsage.ip_address == client_ip)
        )
        if ip_used.scalar_one_or_none():
            raise HTTPException(status_code=429, detail=_UPGRADE_MSG)

        # Block by email (lifetime) — catches same person on a different network
        email_count = await db.execute(
            select(func.count()).where(Submission.email == req.email)
        )
        if (email_count.scalar() or 0) >= 1:
            raise HTTPException(status_code=429, detail=_UPGRADE_MSG)
    else:
        # Paid tier: verify payment record exists for this email
        paid_check = await db.execute(
            select(PaidOrder).where(
                PaidOrder.email == req.email,
                PaidOrder.tier  == req.tier,
                PaidOrder.paid  == True,
            )
        )
        if not paid_check.scalar_one_or_none():
            raise HTTPException(
                status_code=402,
                detail=f"UPGRADE_REQUIRED: No payment found for the {req.tier.title()} plan. Please complete your purchase first.",
            )

    # Enforce account count for tier
    tier_limit = TIER_ACCOUNT_LIMITS.get(req.tier, 1)
    valid_accounts = [a for a in req.accounts if a.handle.strip()]
    if len(valid_accounts) > tier_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Your plan allows up to {tier_limit} account(s). Upgrade to add more.",
        )

    submission = Submission(
        name        = req.name,
        email       = req.email,
        country     = req.country,
        accounts    = [a.model_dump() for a in req.accounts],
        reason      = req.reason,
        timeline    = req.timeline,
        tier        = req.tier or "free",
        lead_status = "paid" if req.tier and req.tier != "free" else "new",
    )
    db.add(submission)
    await db.flush()

    report = Report(submission_id=submission.id, status="queued")
    db.add(report)

    # Record IP for free tier so this device can never get another free scan
    if is_free:
        db.add(FreeIPUsage(ip_address=client_ip))

    await db.commit()
    await db.refresh(report)

    # Pass plain dict — avoids SQLAlchemy session issues in background task
    submission_data = {
        "name":     req.name,
        "email":    req.email,
        "country":  req.country,
        "reason":   req.reason,
        "timeline": req.timeline,
        "accounts": [a.model_dump() for a in req.accounts],
    }

    background_tasks.add_task(run_screening_job, report.id, submission_data)

    # Log lead to Google Sheets (fire-and-forget, never blocks response)
    accounts_str = " | ".join(
        f"{a.platform}: {a.handle}" for a in req.accounts if a.handle.strip()
    )
    background_tasks.add_task(_log_lead_to_sheets, {
        "timestamp":  datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "name":       req.name,
        "email":      req.email,
        "country":    req.country,
        "accounts":   accounts_str,
        "reason":     req.reason,
        "timeline":   req.timeline,
        "job_id":     report.id,
    })

    return {"job_id": report.id, "status": "queued"}


@router.get("/status/{job_id}")
async def get_status(job_id: str, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Job not found.")
    return {
        "job_id": job_id,
        "status": report.status,
        "error":  report.error_message,
    }
