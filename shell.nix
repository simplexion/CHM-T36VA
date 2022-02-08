{ pkgs ? import <nixpkgs> { }, ... }:

with pkgs;
let
  my-python-packages = python3Packages: with python3Packages; [
    jinja2
  ];
  python-with-my-packages = python3.withPackages my-python-packages;
in
mkShell {
  buildInputs = [
    python-with-my-packages
  ];
}
