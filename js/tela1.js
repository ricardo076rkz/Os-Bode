const form = document.getElementById('form-login');
const botao = form.querySelector('.botao');

// Mostrar / ocultar senha
const campoSenha = document.getElementById('password');
const botaoOlho = document.getElementById('ver-senha');

if (campoSenha && botaoOlho) {
  botaoOlho.addEventListener('click', () => {
    const mostrando = campoSenha.type === 'text';
    campoSenha.type = mostrando ? 'password' : 'text';
    botaoOlho.setAttribute('aria-label', mostrando ? 'Mostrar senha' : 'Ocultar senha');
  });
}

// Envio do login
form.addEventListener('submit', e => {
  e.preventDefault();
  const email = form.email.value.trim();
  const senha = form.password.value;
  console.log('Login:', email, senha.length);
  // Aqui entra o fetch para o back-end
});

// Mostra uma mensagem de erro acima do botão
function mostrarErro(msg) {
  let erro = document.getElementById('erro-login');
  if (!erro) {
    erro = document.createElement('p');
    erro.id = 'erro-login';
    erro.style.cssText = 'color:#b91c1c;font-size:.85rem;margin:8px 0;';
    botao.before(erro);
  }
  erro.textContent = msg;
}

function limparErro() {
  const erro = document.getElementById('erro-login');
  if (erro) erro.remove();
}

form.addEventListener('submit'), async e => {
  e.preventDefault();
  limparErro();

  const email = form.email.value.trim();
  const senha = form.password.value;

  if (!email.includes('@')) {
    return mostrarErro('Digite um e-mail válido.');
  }
  if (senha.length < 6) {
    return mostrarErro('A senha deve ter pelo menos 6 caracteres.');
  }

  botao.disabled = true;
  botao.textContent = 'Entrando...';

  try {
    const resposta = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, senha })
    });
    if (!resposta.ok) throw new Error('E-mail ou senha incorretos.');
  } catch (erro) {
    mostrarErro(erro.message);
  } finally {
    botao.disabled = false;
    botao.textContent = 'Entrar';
  }
  if (acessosemlogin) {
    acessosemlogin.addEventListener('click', () => { e.preventDefault();
      window.location.href='home.html';
});
}
}