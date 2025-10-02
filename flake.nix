{
  inputs = {
    utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, nixpkgs, utils }: utils.lib.eachDefaultSystem (system:
    let
      pkgs = nixpkgs.legacyPackages.${system};
    in
      {
        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [
            uv
            pkgs.zlib
            pkgs.stdenv.cc.cc.lib
          ];

          LD_LIBRARY_PATH = "${pkgs.lib.makeLibraryPath [
            pkgs.gcc-unwrapped.lib
            pkgs.zlib
          ]}:$LD_LIBRARY_PATH";

          UV_PYTHON_PREFERENCE = "managed";
          # shellHook = ''
          # '' ;
        };
      }
  );

}
