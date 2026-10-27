"""Limited language-aware evidence vocabulary; original quotes are never translated."""
WORDS={
 'hi':{'work':('काम','नौकरी','कार्यालय'),'connection':('दोस्त','परिवार','अकेला','अकेली'),'rest':('नींद','आराम','थका','थकी'),'daily_routine':('दिनचर्या','टहलने','व्यायाम')},
 'mr':{'work':('काम','नोकरी','कार्यालय'),'connection':('मित्र','कुटुंब','एकटे'),'rest':('झोप','विश्रांती','थकवा'),'daily_routine':('दिनक्रम','चालणे','व्यायाम')},
}
FEELINGS={
 'hi':{'calm':('शांत',),'happy':('खुश',),'sad':('उदास',),'anxious':('चिंतित',),'angry':('गुस्सा',),'grateful':('आभारी',),'hopeful':('आशावान',),'tired':('थका','थकी'),'lonely':('अकेला','अकेली'),'overwhelmed':('अभिभूत',)},
 'mr':{'calm':('शांत',),'happy':('आनंदी',),'sad':('उदास',),'anxious':('चिंतित',),'angry':('राग',),'grateful':('कृतज्ञ',),'hopeful':('आशावादी',),'tired':('थकवा','थकलो','थकले'),'lonely':('एकटे',),'overwhelmed':('भारावून',)},
}


def topic_words(theme,language,base): return tuple(base)+WORDS.get(language,{}).get(theme,())


def explicit_feeling(text,emotion,language):
    import re
    words=FEELINGS.get(language,{}).get(emotion,())
    if not words: return False
    context=r'(?:मैं|मुझे)\s+.{0,20}' if language=='hi' else r'(?:मी|मला)\s+.{0,20}'
    return any(re.search(context+re.escape(word),text) for word in words)
