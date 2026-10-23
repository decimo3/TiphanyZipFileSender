''' Script to read ZIP files and merge PDF '''
import os
import sys
import zipfile
import base64
import logging
from logging import handlers
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv
from pypdf import PdfWriter, PdfReader

class FolderNotFoundError(OSError):
    ''' File not found. '''

class IncorrectArgumentError(BaseException):
    ''' Arguments does not fit to expected (count, value or type) '''

class MissingContentError(BaseException):
    ''' Expected content not found or on insufficient count '''

EXPECTED_ARGUMENT_COUNT = 3

BASE_FOLDER: Path = Path(
    os.path.dirname(sys.executable)
    if getattr(sys, 'frozen', False) else
    os.path.dirname(os.path.abspath(__file__))
)

if __name__ == '__main__':
    exit_code = 0
    logs_path = BASE_FOLDER / 'logs'
    if not logs_path.exists():
        logs_path.mkdir(exist_ok=True)
    logs_path = logs_path / 'zip_bot.log'
    logger = logging.getLogger(__name__)
    log_format = logging.Formatter('%(asctime)-15s %(levelname)-2s %(message)s')
    log_handler = logging.FileHandler(
        filename=logs_path,
        encoding='utf-8',
    )
    log_handler.setFormatter(log_format)
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)
    try:
        logger.info('Iniciando aplicação zip_bot...')
        logger.info('Diretório base: %s', BASE_FOLDER)
        logger.info('Registros salvos em %s', logs_path)
        load_dotenv(BASE_FOLDER / '.env')
        ZIP_FOLDER_PATHS = os.environ.get('ZIP_FOLDER_PATHS')
        logger.info("ZIP_FOLDER_PATHS: %s", ZIP_FOLDER_PATHS)
        if not ZIP_FOLDER_PATHS:
            raise FolderNotFoundError(
                '500: A pasta raiz não foi configurada!',
                'ZIP_FOLDER_PATHS: ' + str(ZIP_FOLDER_PATHS)
            )
        ZIP_FOLDER_PATHS = Path(ZIP_FOLDER_PATHS)
        if not ZIP_FOLDER_PATHS.exists():
            raise FolderNotFoundError(
                '503: A pasta raiz não está acessível! ',
                'ZIP_FOLDER_PATHS: ' + str(ZIP_FOLDER_PATHS)
            )
        if len(sys.argv) != EXPECTED_ARGUMENT_COUNT:
            raise IncorrectArgumentError(
                '401: Argumentos insuficientes! ',
                'Argumentos: [' + ', '.join(sys.argv) + ']'
            )
        if sys.argv[1].lower() != 'laudo':
            raise IncorrectArgumentError(
                '401: Aplicação informada é inválida! ',
                'Argumentos: [' + ', '.join(sys.argv) + ']'
            )
        identifier = sys.argv[2]
        if not identifier.isdigit():
            raise IncorrectArgumentError(
                '401: Argumento informado é inválidos! ',
                'Argumentos: [' + ', '.join(sys.argv) + ']'
            )
        filename = ZIP_FOLDER_PATHS / (identifier + '.zip')
        logger.info("Abrindo arquivo: %s", filename)
        if not filename.exists():
            raise FileNotFoundError(
                '404: O arquivo não foi encontrado! ',
                'Caminho: ' + str(filename)
            )
        with zipfile.ZipFile(filename, 'r') as file:
            try:
                comprovante = file.open(identifier + '.pdf')
                boleto = file.open('boleto' + identifier + '.pdf')
            except KeyError as error:
                raise MissingContentError('500: O arquivo zip não tem ambos arquivos') from error
            with comprovante, boleto, BytesIO() as pdf_bytes:
                with PdfWriter() as writer:
                    for document in {comprovante, boleto}:
                        with PdfReader(document) as reader:
                            if reader.get_num_pages() < 1:
                                raise MissingContentError('500: O arquivo não pode ser lido!')
                            writer.append(reader)
                    writer.write(pdf_bytes)
                logger.info("PDF combinado! Preparando Base64...")
                result = base64.b64encode(pdf_bytes.getvalue()).decode('utf-8')
                logger.info("Base64 gerado: %d caracteres", len(result))
                print(result, flush=True)
    except (FolderNotFoundError, IncorrectArgumentError, MissingContentError) as e:
        logger.error(e.args)
        print(e.args[0], file=sys.stderr)
        exit_code = 1
    except BaseException as e:
        logger.error('500: Aconteceu um erro ao obter o documento: %s', e)
        print('500: Aconteceu um erro ao obter o documento!', file=sys.stderr)
        exit_code = 1
    logger.info('Programa encerrado!')
    sys.exit(exit_code)
