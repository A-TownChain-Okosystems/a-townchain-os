"""
atcpkg Registry & Installer — Issue #30 (Kap. 43)
REST API für das atcpkg Package Management System.
"""
from flask import Blueprint, jsonify, request
from atcpkg.manager import ATCPackageManager, ATCPackage
import time

bp  = Blueprint("atcpkg", __name__, url_prefix="/api/atcpkg")
mgr = ATCPackageManager()

@bp.route("/packages")
def list_packages():
    q = request.args.get("q","")
    if q:
        pkgs = mgr.search(q)
    else:
        pkgs = list(mgr._packages.values())
    return jsonify([{"name":p.name,"version":p.version,"description":p.description,
                     "layer":p.layer,"verified":p.verified,"downloads":p.downloads}
                    for p in pkgs])

@bp.route("/packages/<name>")
def package_info(name):
    pkg = mgr.info(name)
    if not pkg: return jsonify({"error":"Not found"}), 404
    return jsonify({"name":pkg.name,"version":pkg.version,
                    "description":pkg.description,"author":pkg.author,
                    "layer":pkg.layer,"cid":pkg.cid,"deps":pkg.deps,
                    "verified":pkg.verified,"downloads":pkg.downloads})

@bp.route("/install", methods=["POST"])
def install():
    data = request.get_json() or {}
    name = data.get("name","")
    if not name: return jsonify({"error":"name required"}), 400
    try:
        ok = mgr.install(name)
        return jsonify({"installed": ok, "package": name})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@bp.route("/installed")
def installed():
    pkgs = mgr.list_installed()
    return jsonify([p.name for p in pkgs])

@bp.route("/stats")
def stats():
    return jsonify(mgr.stats())
