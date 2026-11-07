  const form = document.getElementById('form-login');
const camposVendedor = document.getElementById('campos-vendedor');
const botao = form.querySelector('.botao');

function atualizarPerfil() {
  const perfil = form.querySelector('input[name="perfil"]:checked').value.toLowerCase();
  const ehVendedor = perfil === 'vendedor';

  camposVendedor.classList.toggle('aberto', ehVendedor);
  if (form.banca) form.banca.required = ehVendedor;
  botao.textContent = ehVendedor ? 'Entrar como vendedor' : 'Entrar';
}

form.querySelectorAll('input[name="perfil"]').forEach(radio => {
  radio.addEventListener('change', atualizarPerfil);
});

atualizarPerfil();