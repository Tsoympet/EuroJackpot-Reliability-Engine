# Manual GitHub Upload

## Recommended repository

Create a new repository named:

```text
EuroJackpot-Reliability-Engine
```

A separate repository is safer than merging these files into `ultra-lottery-helper`, which already contains a different application.

## Upload the source repository

1. Extract `EuroJackpot_GitHub_Manual_Upload_v3_8.zip`.
2. Open:
   `repository/EuroJackpot-Reliability-Engine-v3.8/`
3. On GitHub, create the new repository.
4. Select **Add file → Upload files**.
5. Drag **all contents inside** the repository folder into the upload page.
6. Commit with:
   `Initial EuroJackpot Reliability Engine v3.8 release`

Do not upload the outer `repository` folder itself unless you deliberately want an extra directory level.

## Upload installer assets as a GitHub Release

After the repository commit:

1. Open **Releases**.
2. Choose **Draft a new release**.
3. Tag: `v3.8.0`
4. Title: `EuroJackpot Reliability Engine v3.8`
5. Upload from `release-assets/`:
   - `EuroJackpot_Engine_v3_8_Windows_Installer.zip`
   - `eurojackpot-engine_3.8.0_all.deb`
   - `EuroJackpot_Engine_v3_8_Desktop_Source.zip`
6. Publish the release.

## Public or private

Use **Private** while reviewing the code and documentation. Change it to **Public** after confirming that no private data, credentials or unwanted historical artifacts are present.

## Git command alternative

```bash
git init
git add .
git commit -m "Initial EuroJackpot Reliability Engine v3.8 release"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/EuroJackpot-Reliability-Engine.git
git push -u origin main
```
