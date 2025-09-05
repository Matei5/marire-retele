## Tunel DNS
În cadrul acestei teme veți avea de implementat un client și un server care vor utiliza pachete DNS malformate pentru a crea un tunel prin care se pot transmite informații arbitrare.
Este un atac destul de [periculos](https://www.catchpoint.com/network-admin-guide/dns-tunneling) iar această temă are scopul de a vă familiariza cu principiile acestui atac cu scopul de a putea crea metode de protecție pe rețelele cu care veți lucra. Nu încercați să reproduceți metoda pe rețele publice, există [o groază de mijloace](https://www.prosec-networks.com/en/blog/dns-tunneling-erkennen/) prin care se poate descoperi tipul acesta de trafic pe rețea.

Ca model, puteți să vă inspirați din aplicații care fac deja asta, cum ar fi [dnstt](https://www.bamsoftware.com/software/dnstt/), [iodine](https://github.com/yarrick/iodine) și multe altele.


În cele ce urmează vom presupune că lucrăm cu VPS de la Oracle Cloud. Principiile sunt aceleași și dacă alegeți alt tip de cloud sau chiar self-hosting.

1. Citiți despre tuneluri DNS pe pagina https://dnstunnel.de și pe pagina despre [mitigare](https://www.prosec-networks.com/en/blog/dns-tunneling-erkennen/)
1. Deschideți portul UDP 53 pentru conexiuni din exterior, pe OCI trebuie deschis și din [iptables](https://judexzhu.github.io/Iptables-Basic-Knowledge/) și din [rețeaua virtuală VCN](https://stackoverflow.com/a/63648081): `sudo sudo iptables -I INPUT 6 -p udp -m udp --dport 53 -j ACCEPT && sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8080 -j ACCEPT && sudo netfilter-persistent save` mai multe despre [iptables si aici](https://www.digitalocean.com/community/tutorials/iptables-essentials-common-firewall-rules-and-commands)
1. Pentru a verifica că merge conexiunea, porniți serverul DNS de la punctul anterior și testați-l cu dig, dar opriți resolverul existent `systemctl start systemd-resolved`
1. Configurați intrări NS și A ca în exemplul de pe https://dnstunnel.de și testați cu dig că se face rezolvarea numelor în mod corect 
1. Modificați codul de DNS server de la punctul anterior pentru a putea cere și transfera un fișier de la server la client folosind pachete malformate DNS, modificând query si response packet, [exemplu aici](https://dnstunnel.de/#communication); clientul poate trimite cerere pentru un nume_fisier.domeniu.tunel.live iar serverul răspunde cu pachete TXT care contin fisierul pe bucăți codificat binar
1. Atenție că datele transmise prin protocolul UDP se pot pierde, **trebuie să aveți un stop and wait sau fereastră glisantă prin care să vă asigurați că tot fișierul ajunge la destinație**; la demo veți prezenați [md5 checksum](https://www.tecmint.com/generate-verify-check-files-md5-checksum-linux/) pentru fișier; programul trebuie să își continue starea și dacă pierdeți conexiunea de rețea în timp ce faceți transferul
1. În cazul în care nu puteți rezolva punctul anterior, primiți 1p pe exercițiul acesta dacă copiați fișierul cu secury copy (scp) folosind o unealtă de DNS tunnelling existentă (iodine, dnstt, ozymandns etc).
