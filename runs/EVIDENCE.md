# Official test evidence log

Fill this while recording the demo. Also press **Save TC\* evidence** in the Safety tab so SQLite stores the same facts.

## TC1 | Publish supported Indian Sign Language signs

- Input: open **TC1 Supported signs**
- Expected: page titled Indian Sign Language (ISL); 10 glosses with English, Hindi, how-to
- Actual:
- Evidence (screenshot / commit):
- Status: pending / pass / fail / difference

## TC2 | Recognize a supported sign and speak it in two languages

- Input: consent on; perform HELLO (open palm, wave); Classify; Approve & speak EN + HI
- Expected: gloss HELLO; audio in English and Hindi
- Actual:
- Providers (verbx vs fallback):
- Evidence:
- Status:

## TC3 | Transcribe speech and reverse route

- Input: say “thank you” or “धन्यवाद”; correct transcript if needed; Map to supported sign
- Expected: STT text; ISL THANK YOU card. For “where is the station?” → unsupported phrase
- Actual:
- Evidence:
- Status:

## TC4 | Unknown signs + consent

- Input A: camera tab with no consent
- Expected A: Camera blocked
- Input B: consent granted; random wave; Classify
- Expected B: UNRECOGNIZED; Approve & speak disabled
- Actual:
- Evidence:
- Status:
