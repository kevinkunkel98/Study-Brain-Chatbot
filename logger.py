import logging
from enum import Enum
import os

class Mode(Enum):
    NONE = 1
    FULL = 2
    ALLINONE = 3
    ALLSEPARATE = 4

class FeedbackType(Enum):
    CORRECTNESS = 1
    COMPREHENSIBILITY = 2
    RELEVANCE = 3
    INTEGRATION_OF_INFORMATION = 4
    SIZE = 5

class LoggerWrapper:
    def __init__(self, used_mode: Mode = Mode.FULL):
        # for all logs
        self.logger_allinone = self.__create_logger('allinone', 'logs/allinone.csv')
        # for only the logs for the specific type
        self.logger_tokens = self.__create_logger('tokens', 'logs/tokens.csv')
        self.logger_speed = self.__create_logger('speed', 'logs/speed.csv')
        self.logger_feedback = self.__create_logger('feedback', 'logs/feedback.csv')
        # for the complete questions and answers
        self.saver_complete_message = self.__create_logger('complete_message', 'logs/complete_message.csv')

        self.curr_mode = Mode.FULL
        self.curr_mode = used_mode

    def __create_logger(self, name: str, filename: str):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s;%(asctime)s;%(name)s;%(message)s')
        if not os.path.exists(filename):
            if not os.path.exists('logs'):
                os.makedirs('logs')
            with open(filename, 'x') as file:
                print('created log {filename}')
        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def log_tokens(self,prompt_version: str,  id: int, prompt_tokens: int, completion_tokens: int):
        message = f'{prompt_version};{id};TOKENS;{prompt_tokens + completion_tokens}'
        self.log(message, self.logger_tokens)

    def log_speed(self,prompt_version: str,  id: int, start_time: int, end_time: int):
        message = f'{prompt_version};{id};TIME;{end_time - start_time}'
        self.log(message, self.logger_speed)

    def log_feedback(self,prompt_version: str,  id: int, feedback: str, feedback_type: FeedbackType):
        message = f'{prompt_version};{id};{feedback_type};{feedback}'
        self.log(message, self.logger_feedback)


    def log_complete_response(self, prompt_version: str,  id: int, tokens_input: int, start_time: int, end_time: int, tokens_output: int,  question: str,answer: str):
        message = f'{prompt_version};{id};FULL;{tokens_input};{tokens_output};{end_time - start_time};{question};{answer}'.replace('\n', ' ')
        self.saver_complete_message.info(message)


    def log(self, message, logger_chosen):
        if self.curr_mode == Mode.FULL:
            self.logger_allinone.info(message)
            logger_chosen.info(message)
        elif self.curr_mode == Mode.ALLSEPARATE:
            logger_chosen.info(message)
        elif self.curr_mode == Mode.ALLINONE:
            self.logger_allinone.info(message)
