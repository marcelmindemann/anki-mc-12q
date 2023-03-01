# Multiple Choice for Anki
#
# Copyright (C) 2018-2022  zjosua <https://github.com/zjosua>
#
# This file is based on template.py from Glutanimate's
# Cloze Overlapper Add-on for Anki
#
# Copyright (C)  2016-2019 Aristotelis P. <https://glutanimate.com/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the license file that accompanied this program
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# NOTE: This program is subject to certain additional terms pursuant to
# Section 7 of the GNU Affero General Public License.  You should have
# received a copy of these additional terms immediately following the
# terms and conditions of the GNU Affero General Public License that
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <https://glutanimate.com/contact/>.
#
# Any modifications to this file must keep this entire header intact.

"""
Manages note type and card templates
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import json
import re

from anki.consts import MODEL_STD
from aqt import Collection, mw

from .config import *
from .packaging import version

aio_model = "MultipleChoice 12Q"
aio_card = "MultipleChoice 12Q"
aio_fields = {
    "question": "Question",
    "title": "Title",
    "qtype": "QType (0=kprim,1=mc,2=sc)",
    "q1": "Q_1",
    "q2": "Q_2",
    "q3": "Q_3",
    "q4": "Q_4",
    "q5": "Q_5",
    "q6": "Q_6",
    "q7": "Q_7",
    "q8": "Q_8",
    "q9": "Q_9",
    "q10": "Q_10",
    "q11": "Q_11",
    "q12": "Q_12",
    "answers": "Answers",
    "sources": "Sources",
    "extra": "Extra 1"
}


def getOptionsJavaScriptFromConfig(user_config):
    """Get OPTIONS string to write into JavaScript on card template.

    Boolean values differ in Python ('True') VS JavaScript ('true') so they
    need to be converted.
    """
    return (
        "const OPTIONS = {\n"
        "    qtable: {\n"
        f"        visible: true,\n"
        f"        colorize: {'true' if user_config['colorQuestionTable'] else 'false'},\n"
        f"        colors: {user_config['answerColoring']}\n"
        "    },\n"
        "    atable: {\n"
        f"        visible: {'false' if user_config['hideAnswerTable'] else 'true'},\n"
        f"        colorize: {'true' if user_config['colorAnswerTable'] else 'false'},\n"
        f"        colors: {user_config['answerColoring']}\n"
        "    }\n"
        "};\n"
    )


def fillTemplateAndModelFromFile(template, model, user_config={}):
    addonFolderName = mw.addonManager.addonFromModule(__name__)
    addonPath = mw.addonManager.addonsFolder() + '/' + addonFolderName + '/'

    if user_config:
        options_java_script = getOptionsJavaScriptFromConfig(user_config)

    with open(addonPath + 'card/front.html', encoding="utf-8") as f:
        template['qfmt'] = f.read()
    with open(addonPath + 'card/back.html', encoding="utf-8") as f:
        back_template = f.read()
        if user_config:
            back_template = re.sub(
                r'const OPTIONS.*?;', options_java_script, back_template, 1, re.DOTALL)
        template['afmt'] = back_template
    with open(addonPath + 'card/css.css', encoding="utf-8") as f:
        model['css'] = f.read()


def addModel(col: Collection):
    """Add add-on note type to collection"""
    models = col.models
    model = models.new(aio_model)
    model['type'] = MODEL_STD
    # Add fields:
    for i in aio_fields.keys():
        fld = models.new_field(aio_fields[i])
        models.add_field(model, fld)
    # Add template
    template = models.new_template(aio_card)

    fillTemplateAndModelFromFile(template, model)

    model['sortf'] = 0  # set sortfield to question
    models.add_template(model, template)
    models.add(model)
    return model


def updateTemplate(col: Collection, user_config={}):
    """Update add-on note templates"""
    print(f"Updating {aio_model} note template")
    model = col.models.by_name(aio_model)
    template = model['tmpls'][0]

    fillTemplateAndModelFromFile(template, model, user_config)

    col.models.save(model)
    return model


def getOrCreateModel():
    model = mw.col.models.by_name(aio_model)
    if not model:
        # create model
        model = addModel(mw.col)
        return model
    model_version = mw.col.get_config('mc_conf')['version']
    if version.parse(model_version) < version.parse(default_conf_syncd['version']):
        return updateTemplate(mw.col)
    return model


def manage_multiple_choice_note_type():
    """Setup add-on config and templates, update if necessary"""
    getSyncedConfig()
    getLocalConfig()
    getOrCreateModel()
    if version.parse(mw.col.get_config("mc_conf")['version']) < version.parse(default_conf_syncd['version']):
        updateSyncedConfig()
    if version.parse(mw.pm.profile['mc_conf'].get('version', 0)) < version.parse(default_conf_syncd['version']):
        updateLocalConfig()


def update_multiple_choice_note_type_from_config(user_config: str):
    """Set options according to saved user's meta.json in the addon's folder"""
    user_config_dict = json.loads(user_config)
    # Editing other add-ons' config also runs this hook.
    # Only update if the config matches anki-mc's config.
    if list(user_config_dict.keys()) == [
        "answerColoring",
        "colorAnswerTable",
        "colorQuestionTable",
        "hideAnswerTable",
    ]:
        updateTemplate(mw.col, user_config_dict)
    return user_config