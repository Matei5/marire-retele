## ARP Spoofing și TCP Hijacking 


## Structura containerelor
Partea asta se rezolvă folosind aceeași structură de containere ca în capitolul3. Pentru a construi containerele, rulăm `docker compose up -d`.
Imaginea este construită pe baza fișierul `docker/Dockerfile`, dacă facem modificări în fișier sau în scripturile shell, putem rula `docker-compose build --no-cache` pentru a reconstrui imaginile containerelor.


### Observații
1. E posibil ca tabelel ARP cache ale containerelor `router` și `server` să se updateze mai greu. Ca să nu dureze câteva ore până verificați că funcționează, puteți să le curățați în timp ce sau înainte de a declanșa atacul folosind [comenzi de aici](https://linux-audit.com/how-to-clear-the-arp-cache-on-linux/) `ip -s -s neigh flush all`
2. Orice bucată de cod pe care o luați de pe net trebuie însoțită de comments în limba română, altfel nu vor fi punctate.
3. Atacurile implementante aici au un scop didactic, nu încercați să folosiți aceste metode pentru a ataca alte persoane de pe o rețea locală.

## TCP Hijacking 

Modificați `tcp_server.py` și `tcp_client.py` din repository `src` și rulați-le pe containerul `server`, respectiv `client` ca să-și trimită în continuu unul altuia mesaje random (generați text sau numere, ce vreți voi). Puteți folosi time.sleep de o secundă/două să nu facă flood. Folosiți soluția de la exercițiul anterior pentru a vă interpune în conversația dintre `client` și `server`.
După ce ați reușit atacul cu ARP spoofing și interceptați toate mesajele, modificați conținutul mesajelor trimise de către client și de către server și inserați voi un mesaj adițional în payload-ul de TCP. Dacă atacul a funcționat atât clientul cât și serverul afișează mesajul pe care l-ați inserat. Atacul acesta se numeșete [TCP hijacking](https://www.geeksforgeeks.org/session-hijacking/) pentru că atacatorul devine un [proxy](https://en.wikipedia.org/wiki/Proxy_server) pentru conexiunea TCP dintre client și server.


### Indicații de rezolvare

1. Puteți urmări exemplul din curs despre [Netfilter Queue](https://networks.hypha.ro/capitolul6/#scapy_nfqueue) pentru a pune mesajele care circulă pe rețeaua voastră într-o coadă ca să le procesați cu scapy. Atenție! netfilterqueu nu va funcționa cu windows sau mac.
2. Urmăriți exemplul [DNS Spoofing](https://networks.hypha.ro/capitolul6/#scapy_dns_spoofing) pentru a vedea cum puteți altera mesajele care urmează a fi redirecționate într-o coadă și pentru a le modifica payload-ul înainte de a le trimite (adică să modificați payload-ul înainte de a apela `packet.accept()`).
4. Verificați dacă pachetele trimise/primite au flag-ul PUSH setat. Are sens să alterați `SYN` sau `FIN`?
5. Țineți cont de lungimea mesajului pe care îl introduceți pentru ajusta `Sequence Number` (sau `Acknowledgement Number`?), dacă e necesar.
6. Încercați întâi să captați și să modificați mesajele de pe containerul router pentru a testa TCP hijacking apoi puteți combina exercițiul 1 cu metoda de hijacking.
7. Scrieți pe teams orice întrebări aveți, indiferent de cât de simple sau complicate vi se par.
