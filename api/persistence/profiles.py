"""`NormalizedProfile`'ı `snapshots` + bağlı `posts` satırlarına yazar."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.adapters.base import NormalizedProfile
from api.models import Post, Snapshot


async def persist_profile(
    session: AsyncSession, business_id: int, profile: NormalizedProfile
) -> Snapshot:
    """Bir snapshot + gönderilerini yazar; aynı veriyi tekrar yazmaz (idempotent).

    Idempotency içerik temellidir: (business_id, source) için en son snapshot'ın ham
    verisi (`raw`) gelen profille aynıysa yeni satır açılmaz, mevcut snapshot döner.
    Böylece BE-9 cache'i sardığında (7 gün) veya bir çekim yanlışlıkla iki kez
    persist edilse bile çift snapshot oluşmaz. Gerçekten değişmiş veri (bir hafta
    sonra) yeni snapshot doğurur — snapshot'lar tarihsel kalır.

    Redis cache burada YAZILMAZ (BE-9'un işi); bu yalnızca DB seviyesinde bir
    idempotency ağıdır.
    """
    latest = await session.scalar(
        select(Snapshot)
        .where(
            Snapshot.business_id == business_id,
            Snapshot.source == profile.source,
        )
        .order_by(Snapshot.captured_at.desc())
        .limit(1)
    )
    if latest is not None and latest.raw == profile.raw:
        return latest

    snapshot = Snapshot(
        business_id=business_id,
        source=profile.source,
        followers=profile.followers,
        follows=profile.follows,
        media_count=profile.media_count,
        biography=profile.biography,
        external_url=profile.external_url,
        is_professional=profile.is_professional,
        raw=profile.raw,
    )
    session.add(snapshot)
    await session.flush()  # snapshot.id gerekli

    session.add_all(
        Post(
            snapshot_id=snapshot.id,
            ig_id=post.ig_id,
            media_type=post.media_type,
            caption=post.caption,
            like_count=post.like_count,
            comment_count=post.comment_count,
            view_count=post.view_count,
            posted_at=post.posted_at,
            permalink=post.permalink,
            thumb_url=post.thumb_url,
        )
        for post in profile.posts
    )
    await session.flush()
    return snapshot
