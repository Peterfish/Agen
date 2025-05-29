import sys
import time
import re
import json
import requests
import traceback

from goat_storytelling_agent import utils
from goat_storytelling_agent.plan import Plan


SUPPORTED_BACKENDS = ["koboldcpp"]  # Only koboldcpp supported


def _query_chat_koboldcpp(endpoint, messages, retries=3, request_timeout=120,
                          max_tokens=4096, extra_options={}):
    """Query KoboldCpp using OpenAI compatible API"""
    endpoint = endpoint.rstrip('/')
    headers = {'Content-Type': 'application/json'}
    
    # Default parameters for Mistral Large
    default_params = {
        'temperature': 0.7,
        'top_p': 0.9,
        'top_k': 40,
        'repetition_penalty': 1.1,
    }
    default_params.update(extra_options)
    
    data = {
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": True,
        **default_params
    }
    
    print(f"\n========== Submitting request to KoboldCpp...")
    sys.stdout.flush()
    
    while retries > 0:
        try:
            response = requests.post(
                f"{endpoint}/chat/completions",
                headers=headers,
                data=json.dumps(data),
                timeout=request_timeout,
                stream=True
            )
            
            result = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith("data: "):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            json_data = json.loads(line[6:])
                            if 'choices' in json_data and len(json_data['choices']) > 0:
                                delta = json_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                result += content
                                print(content, end='')
                                sys.stdout.flush()
                        except json.JSONDecodeError:
                            continue
            
            print("\nDone reading response.")
            return result.strip()
            
        except Exception as e:
            traceback.print_exc()
            print(f'Error: {e}, retrying...')
            retries -= 1
            time.sleep(5)
    
    return ''


class StoryAgent:
    def __init__(self, backend_uri='http://localhost:5001/v1', backend="koboldcpp", 
                 request_timeout=120, max_tokens=4096, n_crop_previous=400,
                 prompt_engine=None, form='novel',
                 extra_options={}, scene_extra_options={}):

        self.backend = backend.lower()
        if self.backend not in SUPPORTED_BACKENDS:
            raise ValueError(f"Backend must be 'koboldcpp', got '{self.backend}'")

        if prompt_engine is None:
            from goat_storytelling_agent import prompts
            self.prompt_engine = prompts
        else:
            self.prompt_engine = prompt_engine

        self.form = form
        self.max_tokens = max_tokens
        
        # Default options optimized for Mistral Large
        default_options = {
            'temperature': 0.8,
            'top_p': 0.9,
            'top_k': 40,
            'repetition_penalty': 1.1,
        }
        default_options.update(extra_options)
        self.extra_options = default_options
        
        # Scene generation might benefit from slightly higher creativity
        scene_defaults = default_options.copy()
        scene_defaults['temperature'] = 0.9
        scene_defaults.update(scene_extra_options)
        self.scene_extra_options = scene_defaults
        
        self.backend_uri = backend_uri
        self.n_crop_previous = n_crop_previous
        self.request_timeout = request_timeout

    def query_chat(self, messages, retries=3, use_scene_options=False):
        options = self.scene_extra_options if use_scene_options else self.extra_options
        
        result = _query_chat_koboldcpp(
            self.backend_uri, messages, retries=retries,
            request_timeout=self.request_timeout,
            max_tokens=self.max_tokens, extra_options=options)
        
        return result

    def parse_book_spec(self, text_spec):
        # Initialize book spec dict with empty fields
        fields = self.prompt_engine.book_spec_fields
        spec_dict = {field: '' for field in fields}
        last_field = None
        if "\"\"\"" in text_spec[:int(len(text_spec)/2)]:
            header, sep, text_spec = text_spec.partition("\"\"\"")
        text_spec = text_spec.strip()

        # Process raw spec into dict
        for line in text_spec.split('\n'):
            pseudokey, sep, value = line.partition(':')
            pseudokey = pseudokey.lower().strip()
            matched_key = [key for key in fields
                           if (key.lower().strip() in pseudokey)
                           and (len(pseudokey) < (2 * len(key.strip())))]
            if (':' in line) and (len(matched_key) == 1):
                last_field = matched_key[0]
                if last_field in spec_dict:
                    spec_dict[last_field] += value.strip()
            elif ':' in line:
                last_field = 'other'
                spec_dict[last_field] = ''
            else:
                if last_field:
                    # If line does not contain ':' it should be
                    # the continuation of the last field's value
                    spec_dict[last_field] += ' ' + line.strip()
        spec_dict.pop('other', None)
        return spec_dict

    def init_book_spec(self, topic):
        """Creates initial book specification

        Parameters
        ----------
        topic : str
            Short initial topic

        Returns
        -------
        List[Dict]
            Used messages for logging
        str
            Book specification text
        """
        messages = self.prompt_engine.init_book_spec_messages(topic, self.form)
        text_spec = self.query_chat(messages)
        spec_dict = self.parse_book_spec(text_spec)

        text_spec = "\n".join(f"{key}: {value}"
                              for key, value in spec_dict.items())
        # Check and fill in missing fields
        for field in self.prompt_engine.book_spec_fields:
            while not spec_dict[field]:
                messages = self.prompt_engine.missing_book_spec_messages(
                    field, text_spec)
                missing_part = self.query_chat(messages)
                key, sep, value = missing_part.partition(':')
                if key.lower().strip() == field.lower().strip():
                    spec_dict[field] = value.strip()
        text_spec = "\n".join(f"{key}: {value}"
                              for key, value in spec_dict.items())
        return messages, text_spec

    def enhance_book_spec(self, book_spec):
        """Make book specification more detailed

        Parameters
        ----------
        book_spec : str
            Book specification

        Returns
        -------
        List[Dict]
            Used messages for logging
        str
            Book specification text
        """
        messages = self.prompt_engine.enhance_book_spec_messages(
            book_spec, self.form)
        text_spec = self.query_chat(messages)
        spec_dict_old = self.parse_book_spec(book_spec)
        spec_dict_new = self.parse_book_spec(text_spec)

        # Check and fill in missing fields
        for field in self.prompt_engine.book_spec_fields:
            if not spec_dict_new[field]:
                spec_dict_new[field] = spec_dict_old[field]

        text_spec = "\n".join(f"{key}: {value}"
                              for key, value in spec_dict_new.items())
        return messages, text_spec

    def create_plot_chapters(self, book_spec):
        """Create initial by-plot outline of form

        Parameters
        ----------
        book_spec : str
            Book specification

        Returns
        -------
        List[Dict]
            Used messages for logging
        dict
            Dict with book plan
        """
        messages = self.prompt_engine.create_plot_chapters_messages(book_spec, self.form)
        plan = []
        while not plan:
            text_plan = self.query_chat(messages)
            if text_plan:
                plan = Plan.parse_text_plan(text_plan)
        return messages, plan

    def enhance_plot_chapters(self, book_spec, plan):
        """Enhances the outline to make the flow more engaging

        Parameters
        ----------
        book_spec : str
            Book specification
        plan : Dict
            Dict with book plan

        Returns
        -------
        List[Dict]
            Used messages for logging
        dict
            Dict with updated book plan
        """
        text_plan = Plan.plan_2_str(plan)
        all_messages = []
        for act_num in range(3):
            messages = self.prompt_engine.enhance_plot_chapters_messages(
                act_num, text_plan, book_spec, self.form)
            act = self.query_chat(messages)
            if act:
                act_dict = Plan.parse_act(act)
                while len(act_dict['chapters']) < 2:
                    act = self.query_chat(messages)
                    act_dict = Plan.parse_act(act)
                else:
                    plan[act_num] = act_dict
                text_plan = Plan.plan_2_str(plan)
            all_messages.append(messages)
        return all_messages, plan

    def split_chapters_into_scenes(self, plan):
        """Creates a by-scene breakdown of all chapters

        Parameters
        ----------
        plan : Dict
            Dict with book plan

        Returns
        -------
        List[Dict]
            Used messages for logging
        dict
            Dict with updated book plan
        """
        all_messages = []
        act_chapters = {}
        for i, act in enumerate(plan, start=1):
            text_act, chs = Plan.act_2_str(plan, i)
            act_chapters[i] = chs
            messages = self.prompt_engine.split_chapters_into_scenes_messages(
                i, text_act, self.form)
            act_scenes = self.query_chat(messages)
            act['act_scenes'] = act_scenes
            all_messages.append(messages)

        for i, act in enumerate(plan, start=1):
            act_scenes = act['act_scenes']
            act_scenes = re.split(r'Chapter (\d+)', act_scenes.strip())

            act['chapter_scenes'] = {}
            chapters = [text.strip() for text in act_scenes[:]
                        if (text and text.strip())]
            current_ch = None
            merged_chapters = {}
            for snippet in chapters:
                if snippet.isnumeric():
                    ch_num = int(snippet)
                    if ch_num != current_ch:
                        current_ch = snippet
                        merged_chapters[ch_num] = ''
                    continue
                if merged_chapters:
                    merged_chapters[ch_num] += snippet
            ch_nums = list(merged_chapters.keys()) if len(
                merged_chapters) <= len(act_chapters[i]) else act_chapters[i]
            merged_chapters = {ch_num: merged_chapters[ch_num]
                               for ch_num in ch_nums}
            for ch_num, chapter in merged_chapters.items():
                scenes = re.split(r'Scene \d+.{0,10}?:', chapter)
                scenes = [text.strip() for text in scenes[1:]
                          if (text and (len(text.split()) > 3))]
                if not scenes:
                    continue
                act['chapter_scenes'][ch_num] = scenes
        return all_messages, plan

    @staticmethod
    def prepare_scene_text(text):
        lines = text.split('\n')
        ch_ids = [i for i in range(min(5, len(lines)))
                  if 'Chapter ' in lines[i]]
        if ch_ids:
            lines = lines[ch_ids[-1]+1:]
        sc_ids = [i for i in range(min(5, len(lines)))
                  if 'Scene ' in lines[i]]
        if sc_ids:
            lines = lines[sc_ids[-1]+1:]

        placeholder_i = None
        for i in range(len(lines)):
            if lines[i].startswith('Chapter ') or lines[i].startswith('Scene '):
                placeholder_i = i
                break
        if placeholder_i is not None:
            lines = lines[:i]

        text = '\n'.join(lines)
        return text

    def write_a_scene(self, scene, sc_num, ch_num, plan, previous_scene=None):
        """Generates a scene text for a form

        Parameters
        ----------
        scene : str
            Scene description
        sc_num : int
            Scene number
        ch_num : int
            Chapter number
        plan : Dict
            Dict with book plan
        previous_scene : str, optional
            Previous scene text, by default None

        Returns
        -------
        List[Dict]
            Used messages for logging
        str
            Generated scene text
        """
        text_plan = Plan.plan_2_str(plan)
        messages = self.prompt_engine.scene_messages(
            scene, sc_num, ch_num, text_plan, self.form)
        if previous_scene:
            previous_scene = utils.keep_last_n_words(previous_scene,
                                                     n=self.n_crop_previous)
            messages[1]['content'] += f'{self.prompt_engine.prev_scene_intro}\"\"\"{previous_scene}\"\"\"'
        generated_scene = self.query_chat(messages, use_scene_options=True)
        generated_scene = self.prepare_scene_text(generated_scene)
        return messages, generated_scene

    def continue_a_scene(self, scene, sc_num, ch_num,
                         plan, current_scene=None):
        """Continues a scene text for a form

        Parameters
        ----------
        scene : str
            Scene description
        sc_num : int
            Scene number
        ch_num : int
            Chapter number
        plan : Dict
            Dict with book plan
        current_scene : str, optional
            Text of the current scene so far, by default None

        Returns
        -------
        List[Dict]
            Used messages for logging
        str
            Generated scene continuation text
        """
        text_plan = Plan.plan_2_str(plan)
        messages = self.prompt_engine.scene_messages(
            scene, sc_num, ch_num, text_plan, self.form)
        if current_scene:
            current_scene = utils.keep_last_n_words(current_scene,
                                                    n=self.n_crop_previous)
            messages[1]['content'] += f'{self.prompt_engine.cur_scene_intro}\"\"\"{current_scene}\"\"\"'
        generated_scene = self.query_chat(messages, use_scene_options=True)
        generated_scene = self.prepare_scene_text(generated_scene)
        return messages, generated_scene

    def generate_story(self, topic):
        """Example pipeline for a novel creation"""
        _, book_spec = self.init_book_spec(topic)
        _, book_spec = self.enhance_book_spec(book_spec)
        _, plan = self.create_plot_chapters(book_spec)
        _, plan = self.enhance_plot_chapters(book_spec, plan)
        _, plan = self.split_chapters_into_scenes(plan)

        form_text = []
        for act in plan:
            for ch_num, chapter in act['chapter_scenes'].items():
                sc_num = 1
                for scene in chapter:
                    previous_scene = form_text[-1] if form_text else None
                    _, generated_scene = self.write_a_scene(
                        scene, sc_num, ch_num, plan,
                        previous_scene=previous_scene)
                    form_text.append(generated_scene)
                    sc_num += 1
        return form_text
