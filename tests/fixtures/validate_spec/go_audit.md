Forrás: /home/user/project/file.go és ${CIC_WORKDIR}/tools/foo.sh

Feladat: végezz forráskód audit-ot, határozd meg hogy a FooBar funkció implemented
státuszú-e. Futtasd: grep -rn "FooBar" . | grep -v _test.go, majd idézd a hívó
fájl:sor (file:line) helyét, ahol a funkció production kódból hívódik.

Megjegyzés: exit code ≠ sikeres.

Output: output/report.md

Az output tartalmazzon Claim-Evidence táblát: Állítás | Státusz | Bizonyíték | Verifikációs módszer | Kockázat.
