INSTRUÇÕES PARA USO

NOME: Caio Giesteira Cardoso

1. Clonar o Repositório ou Obter os Arquivos
Primeiro, obtenha os arquivos do projeto. Se estiver usando um repositório Git, clone-o usando:

git clone <URL_DO_REPOSITORIO>
cd <NOME_DO_DIRETORIO>

2. Criar e Ativar um Ambiente Virtual
Crie um ambiente virtual para isolar as dependências do projeto:

python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate  # Windows

3. Instalar as Dependências
Instale as dependências do projeto listadas no arquivo requirements.txt:

pip install -r requirements.txt
pip install selenium

4. Configurar o Banco de Dados
Certifique-se de ter um servidor SQL configurado e disponível. Use o seguinte script SQL para criar o banco de dados e tabelas necessárias.flaysk

5. Execute o programa