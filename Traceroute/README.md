## Traceroute 
Traceroute este o metodă prin care putem urmări prin ce routere trece un pachet pentru a ajunge la destinație.
În funcție de IP-urile acestor noduri, putem afla țările sau regiunile prin care trec pachetele.
Înainte de a implementa tema, citiți explicația felului în care funcționează [traceroute prin UDP](https://www.slashroot.in/how-does-traceroute-work-and-examples-using-traceroute-command). Pe scurt, pentru fiecare mesaj UDP care este în tranzit către destinație, atunci când TTL (Time to Live) expiră, senderul primește de la router un mesaj [ICMP](https://en.wikipedia.org/wiki/Internet_Control_Message_Protocol#Header) de tipul [Time Exceeded TTL expired in transit](https://en.wikipedia.org/wiki/Internet_Control_Message_Protocol#Time_exceeded).

1. (0.5p) Modificați fișierul `src/traceroute.py` și implementați o aplicație traceroute complet funcțională.
1. (0.5p) Folosiți un API sau o bază de date care oferă informații despre locația IP-urilor (de ex. [ip-api](https://ip-api.com), [ip2loc](https://ip2loc.com), [ipinfo](https://ipinfo.io) etc.) și apelați-l pentru fiecare IP public pe care îl obțineți.

Creați un raport text /markdown în repository în care:

1. (0.25p) afișați locațiile din lume pentru rutele către mai multe site-uri din regiuni diferite: din Asia, Africa și Australia căutând site-uri cu extensia .cn, .za, .au. Folositi IP-urile acestora.
1. (0.25p) Afișați: Orașul, Regiunea și Țara (acolo unde sunt disponibile) prin care trece mesajul vostru pentru a ajunge la destinație.
1. (0.25p) Executați codul din mai multe locații: **VPS** creat la preambul, de la facultate, de acasă, de pe o rețea publică și salvați toate rutele obținute într-un fișier pe care îl veți prezenta
1. (0.25p) Afișați rutele prin diverse țări pe o hartă folosind orice bibliotecă de plotare (plotly, matplotlib, etc)
