#!/usr/bin/env sh

# abort on errors
set -e

cp ../data/packed/processed.7z ./src/dist/processed-data.7z

# navigate into the build output directory
cd src/dist

# if you are deploying to a custom domain
echo 'csc110.hydev.org' > CNAME

git init
git add -A
git commit -m 'deploy'

# if you are deploying to https://<USERNAME>.github.io/<REPO>
git push -f git@github.com:Hykilpikonna/CSC110-Project.git master:gh-pages

cd -
