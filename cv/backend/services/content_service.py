"""
Content Detection Service using OpenCLIP
Detects subject and content type from screen captures
"""

import base64
import io
import torch
import open_clip
from PIL import Image
import numpy as np


# ── Subject candidates ────────────────────────────────────────────────────────
SUBJECTS = [
    "Mathematics",
    "Physics",
    "Chemistry",
    "Biology",
    "Computer Science",
    "History",
    "Geography",
    "Literature",
    "Economics",
    "English Language",
    "General Science",
]

# ── Content-type candidates ───────────────────────────────────────────────────
CONTENT_TYPES = [
    "quiz or test questions",
    "lecture notes or slides",
    "textbook or reading material",
    "scientific diagram or chart",
    "mathematical formula or equation",
    "programming code or terminal",
    "essay or written assignment",
    "presentation or slideshow",
    "worksheet or exercise",
    "video or multimedia content",
]

# Human-readable labels (parallel to CONTENT_TYPES)
CONTENT_TYPE_LABELS = [
    "Quiz",
    "Lecture Notes",
    "Textbook",
    "Diagram",
    "Formula",
    "Code",
    "Essay",
    "Presentation",
    "Worksheet",
    "Video",
]

# ── CLIP prompt templates ──────────────────────────────────────────────────────
SUBJECT_PROMPT   = "a screenshot showing {} content"
CONTENT_TYPE_PROMPT = "a screenshot showing {}"


class ContentDetectionService:
    """
    OpenCLIP-based content detection.
    Classifies an educational screen capture into a Subject and a Content Type.
    """

    _instance = None          # singleton cache

    def __init__(self):
        self.model  = None
        self.preprocess = None
        self.tokenizer  = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Pre-encoded text features (built lazily after load)
        self._subject_features      = None
        self._content_type_features = None

    # ── Singleton ──────────────────────────────────────────────────────────────
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ContentDetectionService()
            cls._instance.load_model()
        return cls._instance

    # ── Model loading ──────────────────────────────────────────────────────────
    def load_model(self):
        """Load ViT-B-32 with laion2b weights (downloaded once, then cached)."""
        try:
            print("⏳ Loading OpenCLIP ViT-B-32 (laion2b_s34b_b79k)…")
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                "ViT-B-32",
                pretrained="laion2b_s34b_b79k",
            )
            self.model = self.model.to(self.device)
            self.model.eval()
            self.tokenizer = open_clip.get_tokenizer("ViT-B-32")

            # Pre-encode text candidates
            self._subject_features      = self._encode_texts(
                [SUBJECT_PROMPT.format(s) for s in SUBJECTS]
            )
            self._content_type_features = self._encode_texts(
                [CONTENT_TYPE_PROMPT.format(c) for c in CONTENT_TYPES]
            )

            print("✅ OpenCLIP content model loaded")
        except Exception as e:
            print(f"❌ Failed to load OpenCLIP: {e}")
            self.model = None

    # ── Text encoding ──────────────────────────────────────────────────────────
    def _encode_texts(self, texts: list) -> torch.Tensor:
        """Encode a list of text strings into normalised CLIP text features."""
        tokens = self.tokenizer(texts).to(self.device)
        with torch.no_grad():
            features = self.model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True)
        return features  # (N, D)

    # ── Image decoding ─────────────────────────────────────────────────────────
    @staticmethod
    def decode_image(image_b64: str) -> Image.Image:
        """Convert base64 string (data-URI or raw) to PIL Image (RGB)."""
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]
        raw = base64.b64decode(image_b64)
        return Image.open(io.BytesIO(raw)).convert("RGB")

    # ── Core detection ─────────────────────────────────────────────────────────
    def detect(self, image_b64: str) -> dict:
        """
        Classify a screen capture.

        Parameters
        ----------
        image_b64 : str
            Base64-encoded JPEG/PNG screenshot.

        Returns
        -------
        dict
            {
                "subject":      "Mathematics",
                "content_type": "Quiz",
                "subject_confidence":      0.82,
                "content_type_confidence": 0.71
            }
        """
        if self.model is None:
            return self._fallback()

        try:
            pil_img   = self.decode_image(image_b64)
            img_tensor = self.preprocess(pil_img).unsqueeze(0).to(self.device)

            with torch.no_grad():
                img_features = self.model.encode_image(img_tensor)
                img_features = img_features / img_features.norm(dim=-1, keepdim=True)

            # Cosine similarity
            subj_logits = (100.0 * img_features @ self._subject_features.T).softmax(dim=-1)
            ct_logits   = (100.0 * img_features @ self._content_type_features.T).softmax(dim=-1)

            subj_probs = subj_logits[0].cpu().numpy()
            ct_probs   = ct_logits[0].cpu().numpy()

            best_subj_idx = int(np.argmax(subj_probs))
            best_ct_idx   = int(np.argmax(ct_probs))

            return {
                "subject":                SUBJECTS[best_subj_idx],
                "content_type":           CONTENT_TYPE_LABELS[best_ct_idx],
                "subject_confidence":     float(subj_probs[best_subj_idx]),
                "content_type_confidence": float(ct_probs[best_ct_idx]),
            }

        except Exception as e:
            print(f"❌ Content detection error: {e}")
            return self._fallback()

    # ── Fallback ───────────────────────────────────────────────────────────────
    @staticmethod
    def _fallback() -> dict:
        return {
            "subject":                "Unknown",
            "content_type":           "Unknown",
            "subject_confidence":     0.0,
            "content_type_confidence": 0.0,
        }
