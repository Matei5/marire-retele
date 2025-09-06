<a name="http"></a> 
## HTTP service

Scrieți un end-point HTTP care are ca scop partiționarea unui range de IP-uri în subnets în funcție de numărul de noduri și numărul de subrețele cerute. În [prima parte a acestui tutorial](https://witestlab.poly.edu/blog/designing-subnets/) puteți vedea un exemplu de împărțire manuală.

Pentru acest exercițiu va trebui să folosiți un server VPS. Predarea soluției se va face ca aplicație server pe VPS și sursele în repository de github

1) instalați pe VPS toate dependencies de python cu scriptul `docker-install-on-ubuntu.sh`
2) adăugați sursele modificate sau folosite în directorul `http_api`
3) modificați template-ul Rezolvare.md și completați raportul cu cerințele de acolo.


Puteți folosi template-ul [simple_flask.py]() din Capitolul 2 pentru a crea un serviciu HTTP cu o metoda [POST](https://www.w3schools.com/tags/ref_httpmethods.asp). Sau folosiți librăria [fastapi](https://github.com/tiangolo/fastapi) care are integrat și swagger.

Input:
```json
{
   "subnet": "10.189.24.0/24",
   "dim": [10, 10, 100],        
}

// subnet - range-ul de IP-uri initial  
// dim - o lista cu numarul de noduri care trebuie acoperit de fiecare subretea
```

Iar aplicația returnează o împărțire în subrețele în funcție de numărul de elemente de din listă:
```json
{
   "LAN1": "10.189.24.128/28",
   "LAN2": "10.189.24.144/28",
   "LAN3": "10.189.24.0/25"
}
```
În cazul în care împărțirea nu se poate face, returnați o eroare.


### Indicații de rezolvare

#### Cum transformăm adrese în octeți și invers
Adresele IP pot fi transformate în șiruri de octeți (numere) folosind inet_aton sau inet_ntoa:
```python
import socket

IP = '198.10.0.3'
octeti = socket.inet_aton(IP)
print(octeti)
#b'\xc6\n\x00\x03'

for octet in octeti:
    print(octet)
'''
198
10
0
3
'''

ip_string = socket.inet_ntoa(octeti)
print(ip_string)
#'198.10.0.3'

```

#### Cum testăm aplicația
Testați aplicația folosind requests, header-ul trebuie să fie: `{'Content-Type': 'application/json'}` iar datele trebuie transformate cu `json.dumps()`.
```python
header = {'Content-Type': 'application/json'}
data = {'subnet': '10.189.24.0/24', 'dim': [10, 10, 100]}
url = 'http://99.99.99.99' # link-ul catre serverul AWS
response = requests.post(url, headers=header, data=json.dumps(data))
print (response.content)
```

#### Cum executăm scriptul pe serverul VPS
Puteți rula scriptul direct pe server folosind tmux, dar mai întâi trebuie să instalați pip și librăria flask pe server:
```bash
sudo apt-get update
sudo apt install python3-pip
pip3 install flask --user
tmux
python3 http_api/simple_flask.py
# Apas Ctrl+b si apoi d pentru a ma detasa de sesiune
```

Vezi [aici tmux cheatsheet](https://tmuxcheatsheet.com/) sau câteva exemple mai jos: 
```bash
tmux ls - listez toate sesiunile
tmux - creez o noua sesiune cu indicele 0,1,2...
tmux attach -t 0 - ma atasez la sesiunea 0
Ctrl + b apoi apas d - face detach de sesiune
Ctrl + b apoi apas s - face switch de sesiune
Ctrl + b apoi apas [ - pentru scroll up
copy to clipboard - tin apasat Shift, selectez, click dreapta copy
```

#### Cum executăm scriptul din docker pe serverul VPS
Clonăm repository cu tema. Modificăm docker-compose.yml pentru containerul `http_api` ca portul de pe host să fie 80 și de-commentăm partea cu `#command`.
