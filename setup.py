#!/usr/bin/env python3
"""
A-TownChain Monorepo — Setup
K2/K3 Konsolidierung: Unified Python package
"""
from setuptools import setup, find_packages

setup(
    name="a-townchain-os",
    version="1.0.0-dev",
    description="A-TownChain — Unified Monorepo (K3 Konsolidierung)",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        # Core dependencies will be added during K3.12 import path migration
    ],
)
