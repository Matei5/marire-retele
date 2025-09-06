from flask import Flask, request, jsonify
import ipaddress

app = Flask(__name__)

def needed_prefix(hosts):
    # calculeaza prefixul minim /X care poate sustine numarul cerut de hosturi
    need = max(0, int(hosts))
    capacity = 1
    usable = -2
    prefix = 32
    while usable < need:
        capacity <<= 1
        prefix -= 1
        usable = capacity - 2
        if prefix < 0:
            break
    return prefix

def allocate_vlsm(supernet, demands):
    # sorteaza cerintele descrescator pentru a plasa mai intai retelele mari
    indexed = [(int(n), i) for i, n in enumerate(demands)]
    indexed.sort(key=lambda x: x[0], reverse=True)
    free = [supernet]
    result = [None] * len(demands)

    for need_hosts, orig_idx in indexed:
        target_prefix = needed_prefix(need_hosts)
        if target_prefix < 0 or target_prefix > 30:
            raise ValueError("cerinta invalida")

        # cauta primul bloc liber suficient de mare
        chosen_idx = None
        for j, block in enumerate(free):
            if block.prefixlen <= target_prefix and block.network_address in supernet:
                chosen_idx = j
                break
        if chosen_idx is None:
            raise ValueError("nu exista spatiu disponibil")

        block = free.pop(chosen_idx)

        # imparte blocul pana cand se ajunge la prefixul dorit
        while block.prefixlen < target_prefix:
            halves = list(block.subnets(prefixlen_diff=1))
            left, right = halves[0], halves[1]
            block = left
            free.append(right)

        result[orig_idx] = block

    if any(net is None for net in result):
        raise ValueError("eroare la alocare")
    return result

@app.route("/partition", methods=["POST"])
def partition():
    # citeste JSON din request si valideaza formatul
    try:
        data = request.get_json(force=True, silent=False)
    except Exception:
        return jsonify(error="json invalid"), 400
    if not isinstance(data, dict):
        return jsonify(error="json trebuie sa fie obiect"), 400

    subnet = data.get("subnet")
    dims = data.get("dim")

    if not isinstance(subnet, str):
        return jsonify(error="subnet trebuie sa fie string"), 400
    if not isinstance(dims, list) or not all(isinstance(x, int) and x >= 0 for x in dims):
        return jsonify(error="dim trebuie sa fie lista de intregi"), 400

    try:
        supernet = ipaddress.ip_network(subnet, strict=True)
        if not isinstance(supernet, ipaddress.IPv4Network):
            return jsonify(error="doar ipv4 este suportat"), 400
    except Exception:
        return jsonify(error="subnet invalid"), 400

    # incearca sa aloce subretele conform cerintelor
    try:
        allocations = allocate_vlsm(supernet, dims)
    except ValueError as e:
        return jsonify(error=str(e)), 400

    # returneaza raspunsul sub forma LAN1, LAN2, ...
    out = {f"LAN{i+1}": str(net) for i, net in enumerate(allocations)}
    return jsonify(out), 200

@app.route("/health", methods=["GET"])
def health():
    # endpoint simplu pentru verificare server
    return jsonify(status="ok"), 200

app.run(host="0.0.0.0", port=8081)