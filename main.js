/**
 * main.js — SUCESOS y MÁS
 * Lógica del frontend: panel de cotización, navbar, animaciones, alertas.
 */

document.addEventListener('DOMContentLoaded', () => {

  // Navbar scroll
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.classList.toggle('scrolled', window.scrollY > 30);
    }, { passive: true });
  }

  // Menú móvil
  const btnMenu   = document.getElementById('btn-menu');
  const menuMovil = document.getElementById('menu-movil');
  if (btnMenu && menuMovil) {
    btnMenu.addEventListener('click', () => menuMovil.classList.toggle('hidden'));
  }

  // Panel lateral de cotización
  const panel         = document.getElementById('panel-carrito');
  const overlay       = document.getElementById('overlay-carrito');
  const btnAbrir      = document.getElementById('btn-carrito');
  const btnAbrirMovil = document.getElementById('btn-carrito-movil');
  const btnCerrar     = document.getElementById('btn-cerrar-panel');

  function abrirPanel() {
    if (!panel || !overlay) return;
    panel.classList.add('abierto');
    overlay.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }

  function cerrarPanel() {
    if (!panel || !overlay) return;
    panel.classList.remove('abierto');
    overlay.classList.add('hidden');
    document.body.style.overflow = '';
  }

  window.cerrarPanel = cerrarPanel;

  if (btnAbrir)      btnAbrir.addEventListener('click', abrirPanel);
  if (btnAbrirMovil) btnAbrirMovil.addEventListener('click', abrirPanel);
  if (btnCerrar)     btnCerrar.addEventListener('click', cerrarPanel);
  if (overlay)       overlay.addEventListener('click', cerrarPanel);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') cerrarPanel(); });

  // Abrir panel automáticamente si se acaba de agregar un servicio
  const flashExito = document.querySelector('.alerta-exito');
  if (flashExito && flashExito.textContent.includes('agregado')) {
    setTimeout(abrirPanel, 400);
  }

  // Enlace activo en la navbar
  const ruta = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;
    if (href === ruta || (ruta.startsWith(href) && href !== '/')) {
      link.classList.add('activo');
    }
    if (href === '/' && ruta === '/') {
      link.classList.add('activo');
    }
  });

  // Animaciones de entrada al hacer scroll
  const elemAnim = document.querySelectorAll('.animar-entrada');
  if (elemAnim.length > 0) {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          obs.unobserve(e.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -30px 0px' });
    elemAnim.forEach(el => obs.observe(el));
  }

  // Contadores animados (para estadísticas)
  document.querySelectorAll('[data-objetivo]').forEach(el => {
    const obsC = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          animarContador(e.target);
          obsC.unobserve(e.target);
        }
      });
    }, { threshold: 0.6 });
    obsC.observe(el);
  });

  function animarContador(el) {
    const objetivo = parseInt(el.dataset.objetivo, 10);
    const inicio   = performance.now();
    const dur      = 1500;
    const update   = t => {
      const p = Math.min((t - inicio) / dur, 1);
      el.textContent = Math.round((1 - Math.pow(1 - p, 3)) * objetivo).toLocaleString('es-PA');
      if (p < 1) requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
  }

  // Cerrar alertas flash automáticamente
  document.querySelectorAll('.alerta').forEach(alerta => {
    setTimeout(() => {
      alerta.style.transition = 'opacity .4s ease, transform .4s ease';
      alerta.style.opacity = '0';
      alerta.style.transform = 'translateY(-6px)';
      setTimeout(() => alerta.remove(), 400);
    }, 5500);

    const btnX = alerta.querySelector('.btn-cerrar-alerta');
    if (btnX) {
      btnX.addEventListener('click', () => {
        alerta.style.opacity = '0';
        setTimeout(() => alerta.remove(), 300);
      });
    }
  });

  // Confirmar antes de eliminar (admin)
  document.querySelectorAll('.btn-eliminar').forEach(btn => {
    btn.addEventListener('click', e => {
      if (!confirm('¿Seguro que deseas eliminar este elemento? Esta acción no se puede deshacer.')) {
        e.preventDefault();
      }
    });
  });

  // Vista previa de imagen en admin
  const inputImg = document.getElementById('campo-imagen');
  const prevImg  = document.getElementById('prev-imagen');
  if (inputImg && prevImg) {
    inputImg.addEventListener('input', () => {
      const val = inputImg.value.trim();
      if (val) {
        prevImg.src = `/static/images/${val}`;
        prevImg.classList.remove('hidden');
      } else {
        prevImg.classList.add('hidden');
      }
    });
  }

  // Contador de caracteres en el textarea de contenido
  const textarea = document.getElementById('contenido');
  const contador = document.getElementById('contador-chars');
  if (textarea && contador) {
    const actualizar = () => {
      const len = textarea.value.length;
      contador.textContent = `${len}/2000`;
      contador.style.color = len > 1800 ? '#ef4444' : len > 1500 ? '#f59e0b' : '#94a3b8';
    };
    textarea.addEventListener('input', actualizar);
    actualizar();
  }

});