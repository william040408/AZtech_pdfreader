from dataclasses import dataclass
from abc import ABC, abstractmethod

# =========================================================
# Base Class
# =========================================================

@dataclass
class Measurement(ABC):
    """
    모든 측정의 공통 부모 클래스
    """
    name: str
    cat: str = ""
    dv: float = 0.0
    
    @abstractmethod
    def classify(self) -> str:
        """
        OK / UN / UP / NG 판정
        """
        pass

    def is_ng(self) -> bool:
        return self.classify() == "NG"

    def is_ok(self) -> bool:
        return self.classify() == "OK"

    @abstractmethod
    def summary(self) -> str:
        """
        핵심 수치 요약 출력
        """
        pass


# =========================================================
# Nominal-based Measurement (직경, 거리, 위치 등)
# =========================================================

@dataclass
class NominalMeasurement(Measurement):
    nv: float = 0.0
    ut: float = 0.0
    lt: float = 0.0 
    up_limit: float = 0.0  # [추가] 상한선 방
    lo_limit: float = 0.0  # [추가] 하한선 방

    def __post_init__(self):
        # 객체가 만들어지자마자 NV + UT, NV + LT를 계산해서 저장합니다.
        self.up_limit = self.nv + self.ut
        self.lo_limit = self.nv + self.lt

    @property
    def actual_value(self) -> float:
        return self.nv + self.dv

    def classify(self) -> str:
        # 기존 로직 유지 (dv와 ut, lt 비교)
        if self.dv > self.ut or self.dv < self.lt:
            return "NG"
        
        MARGIN_LIMIT = 0.005 
        RATIO_LIMIT = 0.85

        if self.ut > 0:
            margin = self.ut - self.dv
            usage_ratio = self.dv / self.ut if self.ut != 0 else 0
            if margin <= MARGIN_LIMIT or usage_ratio >= RATIO_LIMIT:
                return "UP"

        if self.lt < 0:
            margin = self.dv - self.lt
            usage_ratio = self.dv / self.lt if self.lt != 0 else 0
            if margin <= MARGIN_LIMIT or usage_ratio >= RATIO_LIMIT:
                return "UN"
        
        return "OK"

    def actual(self) -> float:
        return self.nv + self.dv

    def summary(self) -> str:
        return (
            f"[{self.classify():^4}] {self.cat:<8} | {self.name}\n"
            f"       NV: {self.nv:.3f} | UT: {self.ut:.3f} | LT: {self.lt:.3f}\n"
            f"       AV: {self.actual():.3f} | DV: {self.dv:.3f}"
        )   


# =========================================================
# Tolerance-only Measurement (진원도, 흔들림 등)
# =========================================================

@dataclass
class ToleranceMeasurement(Measurement):
    to: float = 0.0
    up_limit: float = 0.0  # [추가]
    lo_limit: float = 0.0  # [추가]

    def __post_init__(self):
        # 흔들림 등은 공차값(to) 자체가 상한선이고, 하한선은 0입니다.
        self.up_limit = self.to
        self.lo_limit = 0.0

    @property
    def actual_value(self) -> float:
        return self.dv

    def classify(self) -> str:
        if self.to <= 0:
            return "NG" if self.dv > 0 else "OK"
        ratio = abs(self.dv) / self.to
        return "NG" if ratio > 1.0 else "OK"

    def summary(self) -> str:
        return (
            f"[{self.classify():^4}] {self.cat:<8} | {self.name}\n"
            f"       TO: {self.to:.3f} | DV: {self.dv:.3f}"
        )