# Guía de Contribuciones a Pronostix

¡Gracias por tu interés en contribuir a Pronostix! Esta guía te ayudará a entender nuestros estándares y proceso de desarrollo.

## 📋 Tabla de contenidos

1. [Código de conducta](#código-de-conducta)
2. [Flujo de trabajo](#flujo-de-trabajo)
3. [Estándares de código](#estándares-de-código)
4. [Cómo reportar bugs](#cómo-reportar-bugs)
5. [Cómo proponer features](#cómo-proponer-features)

## 🤝 Código de conducta

- Sé respetuoso con los demás contribuyentes
- Mantén discusiones constructivas y profesionales
- Reporta comportamientos inapropiados al equipo

## 🔄 Flujo de trabajo

### 1. Fork y clonar el repositorio

```bash
# Hacer fork en GitHub
git clone https://github.com/TU_USUARIO/pronostix.git
cd pronostix
```

### 2. Crear rama de feature

```bash
# Actualiza main
git checkout main
git pull origin main

# Crea rama con nombre descriptivo
git checkout -b feature/descripcion-breve
# o para fixes
git checkout -b fix/descripcion-breve
```

### 3. Hacer cambios

- Sigue los estándares de código (ver abajo)
- Commit frecuentes con mensajes descriptivos
- Ejecuta tests antes de hacer commit

```bash
python manage.py test
```

### 4. Commit y push

```bash
git commit -m "tipo: descripción breve

Descripción más detallada si es necesario.
- Punto 1
- Punto 2
"
git push origin feature/descripcion-breve
```

### 5. Pull Request

- Abre un PR en GitHub
- Describe qué cambios hiciste y por qué
- Referencia issues relacionados (#123)
- Espera revisión del equipo

## 📝 Estándares de código

### Formato de commits

Usamos el formato [Conventional Commits](https://www.conventionalcommits.org/):

```
tipo: descripción

[cuerpo opcional]

[footer opcional]
```

**Tipos válidos:**
- `feat:` nueva funcionalidad
- `fix:` corrección de bug
- `docs:` cambios en documentación
- `style:` cambios de formato (no afecta lógica)
- `refactor:` cambio de código sin agregar feature/fix
- `perf:` mejora de performance
- `test:` agregar o modificar tests
- `chore:` cambios en build, dependencias, config

**Ejemplos:**
```
feat: agregar validación de email en registro

fix: corregir cálculo de IVA en ordenes premium

docs: actualizar guía de instalación

test: cubrir edge cases en CompraService
```

### Estilo Python

- Seguir [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Máximo 88 caracteres por línea (Black)
- Usar type hints cuando sea posible
- Docstrings en todas las clases y métodos públicos

**Ejemplo:**
```python
def calcular_total_con_iva(monto: float, incluir_iva: bool) -> float:
    """Calcula el total incluyendo IVA si aplica.
    
    Args:
        monto: Monto base en pesos
        incluir_iva: Si debe incluir el IVA
        
    Returns:
        float: Monto total con o sin IVA
    """
    if incluir_iva:
        return monto * 1.19
    return monto
```

### Tests

- Escribe tests para nuevas funcionalidades
- Mantén cobertura de tests > 80%
- Nombres descriptivos para tests

```python
def test_compra_pase_exitosa_cuando_evento_existe(self):
    """Test que verifica compra exitosa de pase."""
    evento = crear_evento_dummy()
    resultado = CompraService.comprar_pase(evento.id)
    
    self.assertEqual(resultado.status, "201_CREATED")
    self.assertTrue(evento.usuario_pago)
```

## 🐛 Cómo reportar bugs

### Crear issue

1. Ve a [Issues](https://github.com/jdj40211/pronostix/issues)
2. Haz clic en "New Issue"
3. Selecciona template "Bug report"
4. Completa:

**Título:** Descripción breve del bug

**Descripción:**
```markdown
## Descripción
Breve descripción de qué no funciona.

## Pasos para reproducir
1. Haz esto
2. Luego esto
3. Observa el error

## Comportamiento esperado
Qué debería pasar

## Comportamiento actual
Qué está pasando

## Información del entorno
- OS: Windows 10
- Python: 3.9
- Branch: main
```

## ✨ Cómo proponer features

### Crear issue de feature

1. Ve a [Issues](https://github.com/jdj40211/pronostix/issues)
2. Haz clic en "New Issue"
3. Selecciona template "Feature request"
4. Completa:

```markdown
## Descripción
Qué nueva funcionalidad necesitas

## Motivación
Por qué es importante

## Solución propuesta
Cómo podrías implementarla

## Contexto adicional
Ejemplos, enlaces, etc.
```

## ✅ Checklist antes de hacer PR

- [ ] Mi rama está actualizada con `main`
- [ ] He ejecutado `python manage.py test` y todos pasan
- [ ] He seguido estándares de código (PEP 8)
- [ ] Agregué tests para cambios nuevos
- [ ] Actualicé documentación si necesario
- [ ] Mi commit tiene mensaje descriptivo
- [ ] No incluye cambios no relacionados

## 📞 Contacto

- Abre una issue para preguntas
- Etiqueta `@Camiloesoto`, `@jdj400211` para feedback urgente

---

¡Gracias por contribuir a Pronostix! 🚀
