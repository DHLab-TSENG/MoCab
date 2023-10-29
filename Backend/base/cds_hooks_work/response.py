from dataclasses import asdict, dataclass, field
from typing import List


@dataclass
class Coding(object):
    code: str  # REQUIRED	string	The code for what is being represente
    system: str = ""  # OPTIONAL	string	A codesystem for this code.
    display: str = ""  # OPTIONAL	string	A short, human-readable label to display.


@dataclass
class Source(object):
    label: str  # REQUIRED A short, human-readable label to display for the source of the information displayed on
    # this card. If a url is also specified, this MAY be the text for the hyperlink.
    url: str = ""  # OPTIONAL An optional absolute URL to load (via GET, in a browser context) when a user clicks on
    # this link to learn more about the organization or data set that provided the information on this card. Note
    # that this URL should not be used to supply a context-specific "drill-down" view of the information on this
    # card. For that, use link.url instead.
    icon: str = ""  # OPTIONAL An absolute URL to an icon for the source of this card. The icon returned by this URL
    # SHOULD be a 100x100 pixel PNG image without any transparent regions.
    topic: Coding = field(
        default_factory=list)  # OPTIONAL A topic describes the content of the card by providing a high-level
    # categorization that can be useful for filtering, searching or ordered display of related cards in the CDS
    # client's UI. This specification does not prescribe a standard set of topics.


@dataclass
class Suggestion(object):
    label: str
    uuid: str = ""
    isRecommended: bool = False
    actions: list = field(default_factory=list)


@dataclass
class Action(object):
    type: str  # REQUIRED	string	The type of action being performed. Allowed values are: create, update, delete.
    description: str  # REQUIRED string	Human-readable description of the suggested action MAY be presented to the
    # end-user.
    resource: object = field(default_factory=dict)


@dataclass
class Link(object):
    label: str  # REQUIRED	string	Human-readable label to display for this link (e.g. the CDS Client might render
    # this as the underlined text of a clickable link).
    url: str  # REQUIRED	URL to load (via GET, in a browser context) when a user clicks on this link. Note that
    # this MAY be a "deep link" with context embedded in path segments, query parameters, or a hash.
    type: str  # REQUIRED	string	The type of the given URL. There are two possible values for this field. A type of
    # absolute indicates that the URL is absolute and should be treated as-is. A type of smart indicates that the URL
    # is a SMART app launch URL and the CDS Client should ensure the SMART app launch URL is populated with the
    # appropriate SMART launch parameters.
    appContext: str = ""  # OPTIONAL	string	An optional field that allows the CDS Service to share information
    # from the CDS card with a subsequently launched SMART app. The appContext field should only be valued if the
    # link type is smart and is not valid for absolute links. The appContext field and value will be sent to the
    # SMART app as part of the OAuth 2.0 access token response, alongside the other SMART launch parameters when the
    # SMART app is launched. Note that appContext could be escaped JSON, base64 encoded XML, or even a simple string,
    # so long as the SMART app can recognize it.

    @staticmethod
    def absolute(label: str, url: str, appContext: str = ""):
        return Link(label, url, "absolute", appContext=appContext)

    @staticmethod
    def smart(label: str, url: str, appContext: str = ""):
        return Link(label, url, "smart", appContext=appContext)


@dataclass
class Card(object):
    # https://cds-hooks.org/specification/current/#card-attributes
    indicator: str  # REQUIRED	string	Urgency/importance of what this card conveys. Allowed values, in order of
    # increasing urgency, are: info, warning, critical. The CDS Client MAY use this field to help make UI display
    # decisions such as sort order or coloring.
    summary: str  # REQUIRED	string	One-sentence, <140-character summary message for display to the user inside of
    # this card.
    source: Source  # REQUIRED	object	Grouping structure for the Source of the information displayed on this card.
    # The source should be the primary source of guidance for the decision support the card represents.
    uuid: str = None  # OPTIONAL	string	Unique identifier of the card. MAY be used for auditing and logging cards
    # and SHALL be included in any subsequent calls to the CDS service's feedback endpoint.
    detail: str = None  # OPTIONAL	string	Optional detailed information to display; if provided MUST be represented
    # in (GitHub Flavored) Markdown. (For non-urgent cards, the CDS Client MAY hide these details until the user
    # clicks a link like "view more details...").
    suggestions: List[Suggestion] = field(
        default_factory=list)  # OPTIONAL	array of Suggestions	Allows a service to suggest a set of changes in
    # the context of the current activity (e.g. changing the dose of the medication currently being prescribed,
    # for the medication-prescribe activity). If suggestions are present, selectionBehavior MUST also be provided.
    selectionBehavior: str = None  # OPTIONAL	string	Describes the intended selection behavior of the suggestions
    # in the card. Allowed values are: at-most-one, indicating that the user may choose none or at most one of the
    # suggestions;any, indicating that the end user may choose any number of suggestions including none of them and
    # all of them. CDS Clients that do not understand the value MUST treat the card as an error.
    overrideReasons: List[
        Coding] = None  # OPTIONAL	array of Coding	Override reasons can be selected by the end user when overriding a
    # card without taking the suggested recommendations. The CDS service MAY return a list of override reasons to the
    # CDS client. The CDS client SHOULD present these reasons to the clinician when they dismiss a card. A CDS client
    # MAY augment the override reasons presented to the user with its own reasons.
    links: List[
        Link] = None  # OPTIONAL array of Links	Allows a service to suggest a link to an app that the user might want
    # to run for additional information or to help guide a decision.

    @staticmethod
    def info(summary: str, source: Source, **kwargs):
        return Card("info", summary, source, **kwargs)

    @staticmethod
    def warning(summary, source, **kwargs):
        return Card("warning", summary, source, **kwargs)

    @staticmethod
    def critical(summary, source, **kwargs):
        return Card("critical", summary, source, **kwargs)

    def add_link(self, link: Link):
        if self.links is None:
            self.links = []
        self.links.append(link)

    def to_dict(self):
        return asdict(self)


class Response(object):
    cards: List[Card]
    systemActions: List[Action]
    httpStatusCode: int  # any http code but mainly 200 or 412: The CDS Service is unable to retrieve the necessary
    # FHIR data to execute its decision support, either through a prefetch request or directly calling the FHIR server.
    message: str

    def __init__(self, cards=None, statusCode: int = None):
        if cards is None:
            self.cards = []
        if statusCode is None:
            self.httpStatusCode = 200
        else:
            self.httpStatusCode = statusCode

    def add_card(self, card: Card):
        self.cards.append(card)

    def to_dict(self) -> (dict, int):
        return {"cards": [c.to_dict() for c in self.cards]}
