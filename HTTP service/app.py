from flask import Flask, request, jsonify
import ipaddress

app = Flask(__name__)

@app.route("/")
def root():
    return "HTTP partition service"

def needed_prefix(hosts: int) -> int:
    """Calculeaza cel mai mic prefix /X care permite 'hosts' noduri (IPv4, fara adresele .0 si .255)."""
    value = int(hosts)
    if value < 0:
        raise ValueError("cerinta invalida")

    capacity = 1
    usable = -2
    prefix = 32
    while usable < value:
        capacity <<= 1
        prefix -= 1
        usable = capacity - 2
    return prefix


def allocate_vlsm(supernet: ipaddress.IPv4Network, demands):
    """Aloca subretele folosind VLSM, plasand mai intai cerintele mari."""
    indexed = [(int(n), i) for i, n in enumerate(demands)]
    indexed.sort(key=lambda x: x[0], reverse=True)

    free_blocks = [supernet]
    assignments = [None] * len(demands)

    for need_hosts, original_index in indexed:
        target_prefix = needed_prefix(need_hosts)
        # pentru LAN: nu permitem /31 sau /32
        if target_prefix > 30:
            raise ValueError("cerinta invalida")

        chosen_idx = None
        for j, block in enumerate(free_blocks):
            if block.prefixlen <= target_prefix and block.subnet_of(supernet):
                chosen_idx = j
                break

        if chosen_idx is None:
            raise ValueError("nu exista spatiu disponibil")

        block = free_blocks.pop(chosen_idx)

        while block.prefixlen < target_prefix:
            left, right = list(block.subnets(prefixlen_diff=1))
            block = left
            free_blocks.append(right)

        assignments[original_index] = block

    if any(net is None for net in assignments):
        raise ValueError("eroare la alocare")

    return assignments


@app.route("/partition", methods=["POST"])
def partition():
    # citeste JSON si valideaza formatul
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

    try:
        allocations = allocate_vlsm(supernet, dims)
    except ValueError as e:
        return jsonify(error=str(e)), 400

    response = {f"LAN{i+1}": str(net) for i, net in enumerate(allocations)}
    return jsonify(response), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok"), 200

app.run(host="0.0.0.0", port=8081)