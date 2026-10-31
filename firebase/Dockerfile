FROM node:24-alpine@sha256:ebfe2f90462722a7a4de65e91990e97fe0d401c70e0e762c5b53302f905ec1c1

# Pinned, so every machine and CI run the same emulator; Dependabot doesn't see it, so update
# it by hand.
RUN npm install --global firebase-tools@15.33.0

WORKDIR /firebase

COPY firebase.json .firebaserc ./

EXPOSE 9199 4100

# Users are saved to data/export on shutdown and loaded from it on start. data/ is a volume.
# The emulator runs from inside data/ (it still finds firebase.json one level up), because it
# writes the export to a temporary folder in its working directory and then moves it into
# place, which fails across filesystems.
CMD ["sh", "-c", "mkdir -p data && cd data && if [ -f export/firebase-export-metadata.json ]; then set -- --import=export; fi; exec firebase emulators:start --only auth --project demo-testee --export-on-exit=export \"$@\""]
