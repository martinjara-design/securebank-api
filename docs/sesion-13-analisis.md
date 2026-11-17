# Detección de sustitución de una imagen SecureBank

**Caso:** un atacante sustituye `securebank:v1` por una imagen alterada en el registro.

**Firma e identidad.** Resolver la etiqueta y verificar el digest con Cosign, exigiendo la identidad exacta del workflow autorizado y el emisor OIDC de GitHub Actions. Una firma de otra identidad no autoriza la imagen. También se verifica la attestation CycloneDX y la evidencia de inclusión en el registro de transparencia. En la prueba conservada, el digest firmado pasó y el digest modificado terminó con `no signatures found`.

**Integridad.** Comparar el digest recibido con el aprobado; una etiqueta mutable no identifica contenido inmutable. Firmar el original no firma una imagen derivada: al cambiar el contenido o la configuración cambia el digest. Los manifiestos usan `@sha256:...`, sin resolver de nuevo una etiqueta durante el despliegue.

**Admisión.** El workflow corregido crea un clúster Kind con Kyverno en modo Enforce y failurePolicy Fail. La política exige el registro autorizado, digest, firma de la identidad esperada y attestation del SBOM. El gate de Cosign precede al `kubectl apply`; Kyverno vuelve a verificar al admitir Pods. Una prueba crea una imagen sin firma, confirma su existencia y exige su rechazo por esa política. Controles positivos antes y después distinguen el rechazo legítimo de una caída del webhook. Se comprueba además rollout y salud de la imagen firmada.

**Límites.** Las ejecuciones anteriores demuestran firma y bloqueo en CI. La corrección de despliegue/admisión debe quedar respaldada por su nueva ejecución en Actions antes de declararla aprobada. La política confía en una sola identidad exacta por ejecución; en main exige main. Una firma válida no demuestra ausencia de CVEs ni seguridad de un runner comprometido. SCA, revisión de workflows, procedencia y aislamiento del build siguen siendo necesarios. No se declara un nivel SLSA certificado ni reproducibilidad bit a bit.
