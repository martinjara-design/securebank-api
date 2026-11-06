# Sesión 4 · Ejercicio: análisis del pipeline inseguro

El pipeline `ci.yml` de este repo ya aplica las 4 correcciones. Resumen del ejercicio (`deploy-legacy.yml` entregado por el profesor):

| # | Riesgo | Por qué es peligroso | STRIDE | Corrección aplicada |
|---|---|---|---|---|
| R1 | `permissions: write-all` | Un token comprometido permite modificar el repo y publicar releases | Elevation | `permissions: contents: read`; `security-events: write` solo en el job `sast` |
| R2 | `curl http://… \| sudo bash` | Ejecuta código sin firma ni checksum por HTTP | Tampering | Solo acciones oficiales con versión fija; descargas con `sha256sum -c` (ver job `secret-scan`) |
| R3 | `npm install` sin lockfile | Una dependencia flotante permite ataques de supply chain | Tampering | Dependencias con versión exacta en `requirements*.txt`; SCA en el pipeline |
| R4 | Contraseña en el YAML | Queda en el historial de Git para siempre | Info Disclosure | `${{ secrets.* }}`; Gitleaks bloquea cualquier secreto |

## Checklist de aceptación (Sesión 4)

- [x] `.github/workflows/ci.yml` versionado en `main`
- [x] Etapas checkout · install · build · test · artifact
- [x] Artefacto nombrado con hash de commit, retención 7 días
- [ ] Última ejecución en verde (**verificar en Actions**)
- [ ] Status check obligatorio en PR a `main` (**configurar en Settings → Branches**: `secret-scan`, `build-test`, `sast`, `sca`)
- [x] Sin secretos en el YAML
