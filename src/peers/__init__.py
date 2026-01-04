"""
Peer Network Module

Specialist consultation network for doctors to connect with peers
for second opinions, case discussions, and expert consultations.
"""

from src.peers.models import (
    # Enums
    VerificationLevel,
    ConsultStatus,
    ConsultPriority,
    ConsultType,
    MessageType,
    PaymentStatus,
    CaseVisibility,

    # Specialist Models
    Specialist,
    Expertise,
    Availability,
    ConsultFee,

    # Consultation Models
    ConsultRequest,
    ConsultResponse,
    PeerReview,

    # Case Models
    CaseDiscussion,
    CaseComment,

    # Messaging Models
    ConsultMessage,
    MessageThread,

    # Payment Models
    ConsultPayment,
    SpecialistPayout,

    # Verification Models
    VerificationDocument,
    VerificationRequest,

    # Statistics Models
    SpecialistStats,
    PeerNetworkStats,
)

from src.peers.service import (
    PeerNetworkService,
    get_peer_network_service,
)

__all__ = [
    # Service
    "PeerNetworkService",
    "get_peer_network_service",

    # Enums
    "VerificationLevel",
    "ConsultStatus",
    "ConsultPriority",
    "ConsultType",
    "MessageType",
    "PaymentStatus",
    "CaseVisibility",

    # Specialist Models
    "Specialist",
    "Expertise",
    "Availability",
    "ConsultFee",

    # Consultation Models
    "ConsultRequest",
    "ConsultResponse",
    "PeerReview",

    # Case Models
    "CaseDiscussion",
    "CaseComment",

    # Messaging Models
    "ConsultMessage",
    "MessageThread",

    # Payment Models
    "ConsultPayment",
    "SpecialistPayout",

    # Verification Models
    "VerificationDocument",
    "VerificationRequest",

    # Statistics Models
    "SpecialistStats",
    "PeerNetworkStats",
]
