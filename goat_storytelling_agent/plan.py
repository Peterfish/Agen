"""Unifies all plot forms such as by-chapter and by-scene outlines in a single dict."""
import re
import json


class Plan:
    @staticmethod
    def split_by_act(original_plan):
        """Split text plan into acts with improved error handling"""
        # removes only Act texts with newline prepended soemwhere near
        acts = re.split('\n.{0,5}?Act ', original_plan)
        # remove random short garbage from re split
        acts = [text.strip() for text in acts[:]
                if (text and (len(text.split()) > 3))]
        if len(acts) == 4:
            acts = acts[1:]
        elif len(acts) != 3:
            print(f'Warning: split_by_act found {len(acts)} acts instead of 3')
            # Try alternative splitting
            acts = original_plan.split('Act ')
            if len(acts) == 4:
                acts = acts[-3:]
            elif len(acts) != 3:
                print('Warning: Could not split into exactly 3 acts')
                # Fallback: treat entire plan as one act
                return [original_plan]

        # [act1, act2, act3], [Act + act1, act2, act3]
        if acts[0].startswith('Act '):
            acts = [acts[0]] + ['Act ' + act for act in acts[1:]]
        else:
            acts = ['Act ' + act for act in acts[:]]
        return acts

    @staticmethod
    def parse_act(act):
        """Parse act into chapters with improved handling"""
        act = re.split(r'\n.{0,20}?Chapter .+:', act.strip())
        chapters = [text.strip() for text in act[1:]
                    if (text and (len(text.split()) > 3))]
        
        # If no chapters found, try alternative patterns
        if not chapters:
            # Try with dash prefix
            act_alt = re.split(r'\n\s*-\s*Chapter \d+:', act[0])
            chapters = [text.strip() for text in act_alt[1:]
                        if (text and (len(text.split()) > 3))]
        
        return {'act_descr': act[0].strip(), 'chapters': chapters}

    @staticmethod
    def parse_text_plan(text_plan):
        """Parse text plan with better error handling"""
        if not text_plan:
            print("Warning: Empty text plan provided")
            return []
            
        acts = Plan.split_by_act(text_plan)
        if not acts:
            print("Warning: Could not split plan into acts")
            return []
            
        plan = [Plan.parse_act(act) for act in acts if act]
        plan = [act for act in plan if act.get('chapters')]
        
        if not plan:
            print("Warning: No valid acts with chapters found")
            
        return plan

    @staticmethod
    def normalize_text_plan(text_plan):
        """Normalize text plan format"""
        plan = Plan.parse_text_plan(text_plan)
        if not plan:
            return text_plan  # Return original if parsing fails
        text_plan = Plan.plan_2_str(plan)
        return text_plan

    @staticmethod
    def act_2_str(plan, act_num):
        """Convert specific act to string"""
        text_plan = ''
        chs = []
        ch_num = 1
        for i, act in enumerate(plan):
            act_descr = act.get('act_descr', '')
            if act_descr and not re.search(r'Act \d', act_descr[0:50]):
                act_descr = f'Act {i+1}: ' + act_descr
            elif not act_descr:
                act_descr = f'Act {i+1}:'
            act_descr += '\n'
            
            for chapter in act.get('chapters', []):
                if (i + 1) == act_num:
                    act_descr += f'- Chapter {ch_num}: {chapter}\n'
                    chs.append(ch_num)
                elif (i + 1) > act_num:
                    return text_plan.strip(), chs
                ch_num += 1
            text_plan += act_descr + '\n'
        return text_plan.strip(), chs

    @staticmethod
    def plan_2_str(plan):
        """Convert plan to string with error handling"""
        if not plan:
            return "No plan available"
            
        text_plan = ''
        ch_num = 1
        for i, act in enumerate(plan):
            act_descr = act.get('act_descr', '')
            if act_descr and not re.search(r'Act \d', act_descr[0:50]):
                act_descr = f'Act {i+1}: ' + act_descr
            elif not act_descr:
                act_descr = f'Act {i+1}:'
            act_descr += '\n'
            
            for chapter in act.get('chapters', []):
                act_descr += f'- Chapter {ch_num}: {chapter}\n'
                ch_num += 1
            text_plan += act_descr + '\n'
        return text_plan.strip()

    @staticmethod
    def save_plan(plan, fpath):
        """Save plan to JSON file with error handling"""
        try:
            with open(fpath, 'w', encoding='utf-8') as fp:
                json.dump(plan, fp, indent=4, ensure_ascii=False)
            print(f"Plan saved to {fpath}")
        except Exception as e:
            print(f"Error saving plan: {e}")
