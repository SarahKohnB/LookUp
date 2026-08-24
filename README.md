# Object Detection Model for Person and PPE Kit Identification

Sistema de detecção de objetos baseado em **YOLOv8** para identificar **pessoas** e **itens de Equipamento de Proteção Individual (EPI)** em imagens, útil para monitoramento de segurança em ambientes industriais e canteiros de obra.

O projeto é composto por **dois modelos YOLOv8 independentes**:

| Modelo | Função | Classes detectadas |
|---|---|---|
| **Person Model** | Detecta pessoas na imagem | `person` |
| **PPE Model** | Detecta itens de EPI | `hard-hat`, `gloves`, `mask`, `glasses`, `boots`, `vest`, `ppe-suit`, `ear-protector`, `safety-harness` |

Um script de inferência (`inference.py`) roda os dois modelos sobre as mesmas imagens e gera duas saídas anotadas: uma com as pessoas detectadas e outra com os EPIs detectados.

---

## Sumário

- [Estrutura do repositório](#estrutura-do-repositório)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Uso rápido (inferência com os modelos já treinados)](#uso-rápido-inferência-com-os-modelos-já-treinados)
- [Treinando os modelos do zero](#treinando-os-modelos-do-zero)
  - [1. Preparar o dataset (Pascal VOC → YOLO)](#1-preparar-o-dataset-pascal-voc--yolo)
  - [2. Dividir em treino/validação](#2-dividir-em-treinovalidação)
  - [3. Configurar o arquivo `.yaml`](#3-configurar-o-arquivo-yaml)
  - [4. Treinar](#4-treinar)
- [Resultados dos modelos](#resultados-dos-modelos)
- [Observações e limitações](#observações-e-limitações)
- [Solução de problemas](#solução-de-problemas)

---

## Estrutura do repositório

```
Object-Detection-Model-for-Person-and-PPE-kit-identification-main/
│
├── inference.py                     # Script principal de inferência (CLI)
├── pascalVOC_to_yolo.py             # Conversor de anotações XML (Pascal VOC) -> TXT (YOLO)
├── README.md
├── Report on Person Detection and PPE Detection Models.pdf   # Relatório técnico do projeto
│
├── Weights/                         # Pesos finais prontos para uso
│   ├── Person_Model/best.pt
│   └── PPE_Model/best.pt
│
├── PersonModel/
│   ├── ModelCode/
│   │   ├── model.ipynb              # Notebook de treino do modelo de pessoas
│   │   ├── TrainTest_Split.ipynb    # Notebook para dividir dataset em treino/val
│   │   ├── Voc_To_Yolo.ipynb        # Notebook para converter anotações VOC -> YOLO
│   │   ├── fullData.yaml            # Config do dataset (paths + classes)
│   │   └── runs/detect/...          # Histórico de execuções de treino (logs, gráficos, pesos)
│   └── Result/                      # Métricas e gráficos do treino final escolhido
│
└── PPEModel/
    ├── Model Code/
    │   ├── PPE_model.ipynb          # Notebook de treino do modelo de EPI
    │   ├── TrainTest_Split.ipynb
    │   ├── datafile.yaml            # Config do dataset (paths + classes)
    │   └── runs/detect/...
    └── PPE_Results/                 # Métricas e gráficos do treino final escolhido
```

> As pastas `runs/detect/...` e `Result/` / `PPE_Results/` contêm artefatos gerados automaticamente pelo Ultralytics durante o treino (curvas de precisão/recall, matriz de confusão, `results.csv`, `args.yaml`, imagens de batches de treino/validação, etc.). Servem como histórico e não precisam ser executados novamente.

---

## Pré-requisitos

- **Python** 3.8 ou superior (o README original recomenda 3.6+, mas o `ultralytics` atual exige 3.8+)
- **pip**
- Recomendado: uma GPU com CUDA para treinar mais rápido (a inferência funciona normalmente em CPU)

Bibliotecas usadas no projeto:
- [`ultralytics`](https://docs.ultralytics.com/) (YOLOv8)
- `torch` (PyTorch)
- `opencv-python`
- `scikit-learn` (usado apenas na etapa de split treino/validação)

---

## Instalação

1. Clone ou baixe este repositório e entre na pasta:

```bash
git clone <URL-do-repositorio>
cd Object-Detection-Model-for-Person-and-PPE-kit-identification-main
```

2. (Recomendado) Crie um ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
```

3. Instale as dependências:

```bash
pip install ultralytics opencv-python scikit-learn
```

Isso já instala o PyTorch como dependência do `ultralytics`. Se quiser usar GPU, siga as instruções específicas de instalação do PyTorch com CUDA em https://pytorch.org/get-started/locally/ antes de instalar o `ultralytics`.

---

## Uso rápido (inferência com os modelos já treinados)

Os pesos finais já treinados estão em `Weights/Person_Model/best.pt` e `Weights/PPE_Model/best.pt`. Não é necessário treinar nada para testar o projeto.

O script `inference.py` é executado via linha de comando (CLI) com `argparse` e espera 4 argumentos obrigatórios:

| Argumento | Descrição |
|---|---|
| `--input_dir` | Pasta com as imagens de entrada |
| `--output_dir` | Pasta onde as imagens anotadas serão salvas (precisa existir previamente) |
| `--person_model` | Caminho para o `.pt` do modelo de pessoas |
| `--ppe_model` | Caminho para o `.pt` do modelo de EPI |

### Exemplo (usando os pesos incluídos no repositório)

```bash
mkdir -p Final_Results

python inference.py \
  --input_dir "input" \
  --output_dir "Final_Results" \
  --person_model "Weights/Person_Model/best.pt" \
  --ppe_model "Weights/PPE_Model/best.pt"
```

No Windows (PowerShell/CMD), use caminhos no estilo:

```bash
python inference.py --input_dir "C:\caminho\input" --output_dir "C:\caminho\Final_Results" --person_model "Weights\Person_Model\best.pt" --ppe_model "Weights\PPE_Model\best.pt"
```

### O que o script faz

Para cada imagem encontrada em `--input_dir`, o script:
1. Roda o modelo de pessoas e desenha as caixas verdes (`person`) com a confiança da predição.
2. Roda o modelo de EPI e desenha as caixas vermelhas (EPIs detectados) com a confiança da predição.
3. Salva **duas imagens de saída** por imagem de entrada, em `--output_dir`:
   - `person_<nome_da_imagem>` — apenas detecções de pessoas
   - `ppe_<nome_da_imagem>` — apenas detecções de EPI

> Observação: o script não combina as duas detecções em uma única imagem — ele gera uma imagem separada para cada modelo. Se quiser as duas sobrepostas na mesma imagem, é preciso adaptar o script (basta desenhar ambos os conjuntos de caixas sobre a mesma cópia da imagem original).

---

## Treinando os modelos do zero

Se você quiser treinar os modelos com seu próprio dataset, siga o fluxo abaixo. Os notebooks já existentes no repositório documentam esse fluxo passo a passo.

### 1. Preparar o dataset (Pascal VOC → YOLO)

Se suas anotações estiverem no formato Pascal VOC (`.xml`), use `pascalVOC_to_yolo.py` (ou os notebooks `Voc_To_Yolo.ipynb`) para convertê-las para o formato YOLO (`.txt`).

Antes de rodar, edite as variáveis no final do arquivo `pascalVOC_to_yolo.py`:

```python
voc_dir = 'caminho/para/os/xmls'
output_dir = 'caminho/para/salvar/os/txts'
classes = ['hard-hat','gloves','mask','glasses','boots','vest','ppe-suit','ear-protector','safety-harness']
```

Para o modelo de pessoas, use `classes = ['person']`.

Depois, execute:

```bash
python pascalVOC_to_yolo.py
```

Isso gera um arquivo `.txt` por imagem, no formato YOLO: `classe centro_x centro_y largura altura` (valores normalizados entre 0 e 1).

### 2. Dividir em treino/validação

Use o notebook `TrainTest_Split.ipynb` (presente tanto em `PersonModel/ModelCode/` quanto em `PPEModel/Model Code/`). Ele usa `train_test_split` do `scikit-learn` para separar imagens e labels em pastas `train/` e `val/`:

```python
from split_script import split_dataset  # função definida no próprio notebook

split_dataset(
    image_dir="caminho/para/imagens",
    label_dir="caminho/para/labels_yolo",
    output_dir="caminho/de/saida",
    val_size=0.2,       # 20% para validação
    random_state=42
)
```

Isso cria a estrutura esperada pelo YOLO:

```
output_dir/
├── train/
│   ├── images/
│   └── labels/
└── val/
    ├── images/
    └── labels/
```

### 3. Configurar o arquivo `.yaml`

Cada modelo tem um arquivo de configuração do dataset:

- `PersonModel/ModelCode/fullData.yaml`
- `PPEModel/Model Code/datafile.yaml`

Edite os caminhos `train` e `val` para apontar para as pastas geradas no passo anterior. Exemplo (modelo de EPI):

```yaml
train: /caminho/para/out/train
val: /caminho/para/out/val

nc: 9
names: ['hard-hat','gloves','mask','glasses','boots','vest','ppe-suit','ear-protector','safety-harness']
```

> Os caminhos originais no repositório apontam para pastas locais do autor (`C:/Users/midiy/...`) — **é obrigatório atualizá-los** para os caminhos do seu ambiente antes de treinar.

### 4. Treinar

Abra o notebook correspondente (`model.ipynb` para pessoas, `PPE_model.ipynb` para EPI) ou rode o equivalente em script Python:

```python
from ultralytics import YOLO

# Carrega a arquitetura YOLOv8 nano do zero
model = YOLO("yolov8n.yaml")

# Treina usando o arquivo de configuração do dataset
results = model.train(data="fullData.yaml", epochs=20)   # ou "datafile.yaml" para o modelo de EPI

# Avalia no conjunto de validação
results = model.val()
```

Isso vai gerar automaticamente uma pasta `runs/detect/trainN/` com:
- `weights/best.pt` e `weights/last.pt` (pesos)
- `results.csv` e `results.png` (curvas de treino)
- `confusion_matrix.png`, `PR_curve.png`, `P_curve.png`, `R_curve.png`, `F1_curve.png`
- `args.yaml` (hiperparâmetros usados)

Ao final, copie o `best.pt` desejado para a pasta `Weights/` para usar com `inference.py`.

**Dica:** para partir de pesos pré-treinados na COCO (geralmente converge mais rápido e com melhor desempenho do que treinar do zero), troque `YOLO("yolov8n.yaml")` por `YOLO("yolov8n.pt")`.

---

## Resultados dos modelos

Métricas do treino final de 20 épocas (arquivo `results.csv` de cada modelo):

| Modelo | Precision | Recall | mAP50 | mAP50-95 |
|---|---|---|---|---|
| **Person Model** | 0.66 | 0.34 | 0.47 | 0.23 |
| **PPE Model** | 0.69 | 0.07 | 0.09 | 0.04 |

Gráficos e matrizes de confusão completos estão em:
- `PersonModel/Result/`
- `PPEModel/PPE_Results/`

O relatório técnico completo (metodologia, dataset, discussão dos resultados) está em `Report on Person Detection and PPE Detection Models.pdf`, na raiz do repositório.

---

## Observações e limitações

- **Treino curto (20 épocas) e a partir do zero** (`yolov8n.yaml`, sem pesos pré-treinados): isso explica o desempenho ainda modesto, principalmente o *recall* baixo do modelo de EPI. Para uso em produção, recomenda-se retreinar por mais épocas e/ou partir de pesos pré-treinados (`yolov8n.pt`, `yolov8s.pt`, etc.).
- **Caminhos fixos (hardcoded)**: os notebooks e o `pascalVOC_to_yolo.py` contêm caminhos absolutos do ambiente Windows original do autor (`C:/Users/midiy/...`). Sempre ajuste esses caminhos antes de rodar.
- **`inference.py` gera saídas separadas** para pessoa e EPI (não combina as duas detecções em uma única imagem por padrão).
- As pastas `runs/detect/*` dentro de `ModelCode` / `Model Code` são apenas histórico de várias execuções de treino feitas durante o desenvolvimento — o resultado "oficial" de cada modelo está nas pastas `Result/` e `PPE_Results/`.

---

## Solução de problemas

**`ModuleNotFoundError: No module named 'ultralytics'`**
Instale a biblioteca: `pip install ultralytics`

**Erro ao ler alguma imagem em `inference.py` ("Error reading image ... Skipping")**
O script pula automaticamente arquivos que o OpenCV não consegue abrir (ex.: arquivos corrompidos ou que não são imagens). Confira se o arquivo não está corrompido e se a extensão é suportada (`.jpg`, `.png`, etc.).

**`FileNotFoundError` ao salvar as imagens de saída**
A pasta passada em `--output_dir` precisa existir antes de rodar o script. Crie-a manualmente (`mkdir output_dir`) antes de executar.

**Treino muito lento**
Sem GPU (CUDA), o treino do YOLOv8 pode ser bem lento. Verifique se o PyTorch está detectando a GPU com:
```python
import torch
print(torch.cuda.is_available())
```"# LookUp" 
"# LookUp" 
