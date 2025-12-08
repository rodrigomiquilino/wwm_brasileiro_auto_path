import os
import shutil
import sys
import pandas as pd
import json

# Importa o Motor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    import WWM_Extractor_Files_and_Texts_2 as wwm_core
except ImportError:
    print("ERRO: Motor não encontrado na raiz!")
    sys.exit(1)

# --- CONFIG ---
BASE_FILES = "base_files" # Pasta com os originais (en.bin, diff.bin)
OUTPUT_ROOT = "HD"        # Pasta final para zipar
TSV_FILE = "pt-br.tsv"

# Mapeamento dos arquivos
FILES_MAP = [
    # (Caminho no base_files, Caminho no HD final)
    ("locale/translate_words_map_en.bin",          "locale/translate_words_map_en.bin"),
    # ("locale/translate_words_map_en_diff.bin",     "locale/translate_words_map_en_diff.bin"),
    ("oversea/locale/translate_words_map_en.bin",  "oversea/locale/translate_words_map_en.bin"),
    ("oversea/locale/translate_words_map_en_diff.bin", "oversea/locale/translate_words_map_en_diff.bin"),
]

def build():
    print(">>> INICIANDO BUILD AUTOMÁTICO <<<")
    
    # 1. Carregar Tradução
    print(f"Lendo {TSV_FILE}...")
    try:
        df = pd.read_csv(TSV_FILE, sep='\t', dtype=str).dropna(subset=['OriginalText'])
        trans_dict = dict(zip(df['ID'], df['OriginalText']))
        print(f"Dicionário carregado: {len(trans_dict)} termos.")
    except Exception as e:
        print(f"Erro no TSV: {e}")
        sys.exit(1)

    # 2. Limpar/Criar pasta de saída
    if os.path.exists(OUTPUT_ROOT): shutil.rmtree(OUTPUT_ROOT)
    os.makedirs(OUTPUT_ROOT)

    # 3. Processar Arquivos
    temp_work_dir = "temp_work"
    
    for src_rel, dest_rel in FILES_MAP:
        src_full = os.path.join(BASE_FILES, src_rel)
        dest_full = os.path.join(OUTPUT_ROOT, dest_rel)
        
        if not os.path.exists(src_full):
            print(f"AVISO: Arquivo base sumiu: {src_rel}")
            continue

        print(f"Processando: {src_rel} ...")
        
        # Cria pastas necessárias
        os.makedirs(os.path.dirname(dest_full), exist_ok=True)
        
        # Pasta de trabalho temporária para este arquivo
        file_temp_dir = os.path.join(temp_work_dir, src_rel.replace("/", "_"))
        if os.path.exists(file_temp_dir): shutil.rmtree(file_temp_dir)
        os.makedirs(file_temp_dir)

        # Callback mudo
        def log(x): pass 

        try:
            # A) Extrair o original
            wwm_core.extract_file(src_full, os.path.join(file_temp_dir, "data"), log)
            wwm_core.extract_text(os.path.join(file_temp_dir, "data"), os.path.join(file_temp_dir, "text"), log)
            
            # B) Injetar e Reempacotar (Usando a função in_memory)
            # O arquivo final vai direto para a pasta HD de saída
            wwm_core.full_pack_in_memory(file_temp_dir, trans_dict, dest_full, log)
            
        except Exception as e:
            print(f"FALHA em {src_rel}: {e}")
            sys.exit(1)

    # Limpeza
    if os.path.exists(temp_work_dir): shutil.rmtree(temp_work_dir)
    print(">>> BUILD CONCLUÍDO. PASTA 'HD' PRONTA. <<<")

if __name__ == "__main__":
    build()