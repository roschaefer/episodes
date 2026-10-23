{
  description = "episodes -- blog posts and their videos from one source";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # The computer voices for previews, one per language, see video/episode.py.
        piperVoices = pkgs.linkFarm "piper-voices" (map
          ({ dir, file, sha256 }: {
            name = file;
            path = pkgs.fetchurl {
              url = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/${dir}/${file}";
              inherit sha256;
            };
          })
          [
            { dir = "en/en_US/lessac/medium"; file = "en_US-lessac-medium.onnx"; sha256 = "17q1mzm6xd5i2rxx2xwqkxvfx796kmp1lvk4mwkph602k7k0kzjy"; }
            { dir = "en/en_US/lessac/medium"; file = "en_US-lessac-medium.onnx.json"; sha256 = "184hnvd8389xpdm0x2w6phss23v5pb34i0lhd4nmy1gdgd0rrqgg"; }
            { dir = "de/de_DE/thorsten/medium"; file = "de_DE-thorsten-medium.onnx"; sha256 = "06bqpf3zr0zrcsv10l2r6068wnm3w43n5sifixbvn62iiqnpcr3y"; }
            { dir = "de/de_DE/thorsten/medium"; file = "de_DE-thorsten-medium.onnx.json"; sha256 = "11af4rwiwyd4aicr1x1c1y7inakx094qzj0s78kxnfjkj3kxwjlp"; }
          ]);
      in
      {
        # uv installs the Python packages (pyproject.toml); this shell has
        # everything else they and the build call.
        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.just
            pkgs.uv
            pkgs.python312
            # Manim encodes the video, pydub the placeholder silence.
            pkgs.ffmpeg
            # Turns the diagrams' text into paths, which Manim can draw.
            pkgs.inkscape
            # manim-voiceover imports the sox package, which looks for it.
            pkgs.sox
            # For uv to build pycairo and pyaudio from source.
            pkgs.pkg-config
            pkgs.cairo
            pkgs.pango
            pkgs.portaudio
          ];

          # Piper speaks the previews. Its path only: as a package, its
          # Python libraries would land on PYTHONPATH and break the venv.
          PIPER = "${pkgs.piper-tts}/bin/piper";
          PIPER_VOICES = "${piperVoices}";

          # evdev, which the recorder needs, generates C code from every
          # input header it finds, including the host's /usr/include, which
          # may be newer than the Nix headers it then compiles against.
          DIST_EXTRA_CONFIG = pkgs.writeText "setup.cfg" ''
            [build_ecodes]
            evdev_headers = ${pkgs.lib.concatMapStringsSep ":"
              (header: "${pkgs.linuxHeaders}/include/linux/${header}")
              [ "input.h" "input-event-codes.h" "uinput.h" ]}
          '';

          # uv's own Python downloads don't run everywhere, e.g. on NixOS.
          UV_PYTHON = "${pkgs.python312}/bin/python3.12";
          UV_PYTHON_DOWNLOADS = "never";
          # Wheels like numpy's expect these from the host, and Nix's
          # Python doesn't look there.
          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib pkgs.zlib ];

          # The diagrams' labels are set in Roboto Mono, and Inkscape
          # needs the font to turn them into the same paths as on the blog.
          # Only Nix's fonts and config: the host's may be for a newer
          # fontconfig than Nix's, which then warns about every file.
          FONTCONFIG_FILE = pkgs.writeText "fonts.conf" ''
            <?xml version="1.0"?>
            <!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
            <fontconfig>
              <include ignore_missing="yes">${pkgs.fontconfig.out}/etc/fonts/conf.d</include>
              <dir>${pkgs.roboto-mono}</dir>
              <dir>${pkgs.dejavu_fonts}</dir>
              <cachedir prefix="xdg">fontconfig-episodes</cachedir>
            </fontconfig>
          '';
        };
      });
}
