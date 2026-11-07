// Tela de login (consumidor / vendedor)
const form = document.getElementById('form-login');
const camposVendedor = document.getElementById('campos-vendedor');
const botao = form.querySelector('.botao');

function atualizarPerfil() {
  const perfil = form.querySelector('input[name="perfil"]:checked').value.toLowerCase();
  const ehVendedor = perfil === 'vendedor';

  camposVendedor.classList.toggle('aberto', ehVendedor);

  // os campos extras só são obrigatórios quando o vendedor está escolhido
  camposVendedor.querySelectorAll('input').forEach(function (campo) {
    campo.required = ehVendedor;
  });

  botao.textContent = ehVendedor ? 'Entrar como vendedor' : 'Entrar';
}

form.querySelectorAll('input[name="perfil"]').forEach(function (radio) {
  radio.addEventListener('change', atualizarPerfil);
});

// login ainda sem banco de dados: só leva para a tela certa
form.addEventListener('submit', function (e) {
  e.preventDefault();
  const perfil = form.querySelector('input[name="perfil"]:checked').value.toLowerCase();
  window.location.href = perfil === 'vendedor' ? 'minha_loja.html' : 'explorar.html';
});

atualizarPerfil();
