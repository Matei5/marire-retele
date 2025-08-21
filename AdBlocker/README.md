## Server DNS Ad Blocker
În cadrul acestei teme, veți avea de implementat un blocker de reclame și tracking după modelul [pi-hole](https://pi-hole.net/).

1. Citiți despre DNS în [secțiunea de curs](https://github.com/senisioi/computer-networks/tree/2023/capitolul2#dns).
1. Scrieți codul unei aplicații de tip DNS server. Puteți urmări un tutorial [în Rust aici](https://github.com/EmilHernvall/dnsguide/tree/master) și puteți folosi ca punct de plecare [codul în python disponibil în capitolul 6](https://github.com/senisioi/computer-networks/tree/2023/capitolul6#scapy_dns).
1. Utilizați o listă deja curatoriată de domenii asociate cu [reclame și tracking](https://github.com/anudeepND/blacklist) cu scopul de a bloca acele domenii. De fiecare dată când vine o cerere către serverul vostru pentru domenii din lista respectivă, serverul trebuie să [returneaze IP-ul](https://superuser.com/questions/1030329/better-to-block-a-host-to-0-0-0-0-than-to-127-0-0-1) `0.0.0.0`.
1. Creați o orchestrație docker compose (pe modelul `simple_flask.py` făcut la curs) care să pornească codul vostru în python și să pornească serverul DNS pe localhost (puteți pune chiar pe portul 53).
1. Setați serverul să fie DNS-ul principal pentru calculatorul vostru:
    - [Linux](https://www.linuxfordevices.com/tutorials/linux/change-dns-on-linux)
    - [Windows & MacOS](https://www.hellotech.com/guide/for/how-to-change-dns-server-windows-mac)
1. Dacă accesați un site cu multe reclame (ex. https://www.accuweather.com/) ar trebui să apară curat în browser.
1. Salvați într-un fișier toate cererile pe care le blocați pe parcursul unei zile de navigat pe internet. Încercați să adunați minim 100 de nume blocate.
1. Obțineți niște statistici pentru a verifica câte din numele blocate aparțin unor companii precum google, facebook etc. și care sunt cele mai frecvente companii pe care le blocați. Pentru obținerea statisticilor aveți mai multe variante a) verificați dacă un domeniu conține cuvinte precum `google`, `facebook`, etc. b) verificați dacă name serverul pentru acel domeniu conține numele unor companii c) verificați dacă IP-ul pentru acele domenii sau pentru name server sunt parte dintr-o rețea a vreunei companii. Pentru a afla mai multe informații despre un IP și cine îl deține, puteți folosi reverse DNS (e.g., `dig -x 80.96.21.88 +trace`) sau `whois 80.96.21.209` sau un API precum https://ipinfo.io/
