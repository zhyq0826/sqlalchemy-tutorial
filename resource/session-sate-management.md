# State Management

## Quickie Intro to Object States

It’s helpful to know the states which an instance can have within a session:

- **Transient** - an instance that’s not in a session, and is not saved to the database; i.e. it has no database identity. The only relationship such an object has to the ORM is that its class has a `mapper()` associated with it.

- **Pending** - when you [`add()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.add) a transient instance, it becomes pending. It still wasn’t actually flushed to the database yet, but it will be when the next flush occurs.

- **Persistent** - An instance which is present in the session and has a record in the database. You get persistent instances by either flushing so that the pending instances become persistent, or by querying the database for existing instances (or moving persistent instances from other sessions into your local session).

- **Deleted** - An instance which has been deleted within a flush, but the transaction has not yet completed. Objects in this state are essentially in the opposite of “pending” state; when the session’s transaction is committed, the object will move to the detached state. Alternatively, when the session’s transaction is rolled back, a deleted object moves *back* to the persistent state.

  Changed in version 1.1: The ‘deleted’ state is a newly added session object state distinct from the ‘persistent’ state.

- **Detached** - an instance which corresponds, or previously corresponded, to a record in the database, but is not currently in any session. The detached object will contain a database identity marker, however because it is not associated with a session, it is unknown whether or not this database identity actually exists in a target database. Detached objects are safe to use normally, except that they have no ability to load unloaded attributes or attributes that were previously marked as “expired”.

For a deeper dive into all possible state transitions, see the section [Object Lifecycle Events](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_events.html#session-lifecycle-events) which describes each transition as well as how to programmatically track each one.

- transient instance 不在 session 中，没有持久化，没有数据库主键
- pending transient instance 加入 session，但还没有持久化
- persistent 从数据库加载的对象以及 pending instance 被 flushed 之后
- deleted 调用了 session delete 而且发生了 flush，但是没有发生 commit
- detached 有数据库主键，但是不在 session 中

### Getting the Current State of an Object

获取当前对象的状态

The actual state of any mapped object can be viewed at any time using the [`inspect()`](http://docs.sqlalchemy.org/en/rel_1_1/core/inspection.html#sqlalchemy.inspection.inspect) system:

```
>>> from sqlalchemy import inspect
>>> insp = inspect(my_object)
>>> insp.persistent
True
```

See also

[`InstanceState.transient`](http://docs.sqlalchemy.org/en/rel_1_1/orm/internals.html#sqlalchemy.orm.state.InstanceState.transient)

[`InstanceState.pending`](http://docs.sqlalchemy.org/en/rel_1_1/orm/internals.html#sqlalchemy.orm.state.InstanceState.pending)

[`InstanceState.persistent`](http://docs.sqlalchemy.org/en/rel_1_1/orm/internals.html#sqlalchemy.orm.state.InstanceState.persistent)

[`InstanceState.deleted`](http://docs.sqlalchemy.org/en/rel_1_1/orm/internals.html#sqlalchemy.orm.state.InstanceState.deleted)

[`InstanceState.detached`](http://docs.sqlalchemy.org/en/rel_1_1/orm/internals.html#sqlalchemy.orm.state.InstanceState.detached)

## Session Attributes

session 的属性

The [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) itself acts somewhat like a set-like collection. All items present may be accessed using the iterator interface:

session 就像一个普通的 collection，可以对它进行迭代，判断 object 是否存在

```
for obj in session:
    print(obj)
```

And presence may be tested for using regular “contains” semantics:

```
if obj in session:
    print("Object is present")
```

The session is also keeping track of all newly created (i.e. pending) objects, all objects which have had changes since they were last loaded or saved (i.e. “dirty”), and everything that’s been marked as deleted:

```python
# pending objects recently added to the Session
session.new

# persistent objects which currently have changes detected
# (this collection is now created on the fly each time the property is called)
session.dirty

# persistent objects that have been marked as deleted via session.delete(obj)
session.deleted

# dictionary of all persistent objects, keyed on their
# identity key
session.identity_map
```

(Documentation: [`Session.new`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.new), [`Session.dirty`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.dirty), [`Session.deleted`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.deleted), [`Session.identity_map`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.identity_map)).

## Session Referencing Behavior

Objects within the session are *weakly referenced*. This means that when they are dereferenced in the outside application, they fall out of scope from within the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) as well and are subject to garbage collection by the Python interpreter. **The exceptions to this include objects which are pending, objects which are marked as deleted, or persistent objects which have pending changes on them.** After a full flush, these collections are all empty, and all objects are again weakly referenced.

**session 中的 objects 都是弱引用，pending objects、deleted objects、persistent objects with pending changes 的例外。**

To cause objects in the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) to remain strongly referenced, usually a simple approach is all that’s needed. Examples of externally managed strong-referencing behavior include loading objects into a local dictionary keyed to their primary key, or into lists or sets for the span of time that they need to remain referenced. These collections can be associated with a [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session), if desired, by placing them into the [`Session.info`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.info) dictionary.

创造具有强引用的 session 很简单，把所有的 objects 加入到一个特定 container 即可。

An event based approach is also feasible. A simple recipe that provides “strong referencing” behavior for all objects as they remain within the [persistent](http://docs.sqlalchemy.org/en/rel_1_1/glossary.html#term-persistent) state is as follows:

```python
from sqlalchemy import event

def strong_reference_session(session):
    @event.listens_for(session, "pending_to_persistent")
    @event.listens_for(session, "deleted_to_persistent")
    @event.listens_for(session, "detached_to_persistent")
    @event.listens_for(session, "loaded_as_persistent")
    def strong_ref_object(sess, instance):
        if 'refs' not in sess.info:
            sess.info['refs'] = refs = set()
        else:
            refs = sess.info['refs']

        refs.add(instance)


    @event.listens_for(session, "persistent_to_detached")
    @event.listens_for(session, "persistent_to_deleted")
    @event.listens_for(session, "persistent_to_transient")
    def deref_object(sess, instance):
        sess.info['refs'].discard(instance)
```

Above, we intercept the [`SessionEvents.pending_to_persistent()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/events.html#sqlalchemy.orm.events.SessionEvents.pending_to_persistent),[`SessionEvents.detached_to_persistent()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/events.html#sqlalchemy.orm.events.SessionEvents.detached_to_persistent), [`SessionEvents.deleted_to_persistent()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/events.html#sqlalchemy.orm.events.SessionEvents.deleted_to_persistent) and[`SessionEvents.loaded_as_persistent()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/events.html#sqlalchemy.orm.events.SessionEvents.loaded_as_persistent) event hooks in order to intercept objects as they enter the [persistent](http://docs.sqlalchemy.org/en/rel_1_1/glossary.html#term-persistent) transition, and the [`SessionEvents.persistent_to_detached()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/events.html#sqlalchemy.orm.events.SessionEvents.persistent_to_detached) and[`SessionEvents.persistent_to_deleted()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/events.html#sqlalchemy.orm.events.SessionEvents.persistent_to_deleted) hooks to intercept objects as they leave the persistent state.

The above function may be called for any [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) in order to provide strong-referencing behavior on a per-[`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) basis:

```python
from sqlalchemy.orm import Session

my_session = Session()
strong_reference_session(my_session)
```

It may also be called for any [`sessionmaker`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker):

```python
from sqlalchemy.orm import sessionmaker

maker = sessionmaker()
strong_reference_session(maker)
```

## Merging

[`merge()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.merge) transfers state from an outside object into a new or already existing instance within a session. It also reconciles the incoming data against the state of the database, producing a history stream which will be applied towards the next flush, or alternatively can be made to produce a simple “transfer” of state without producing change history or accessing the database. Usage is as follows:

```python
merged_object = session.merge(existing_object)
```

合并 session 之外的 object state 到 session 中的 object，不存在则创建

When given an instance, it follows these steps:

- It examines the primary key of the instance. If it’s present, it attempts to locate that instance in the local identity map. If the `load=True` flag is left at its default, it also checks the database for this primary key if not located locally.

  >  primary key 存在，根据 primary key 在 local 查找，如果 load=True，local 不存在则查找 db

- If the given instance has no primary key, or if no instance can be found with the primary key given, a new instance is created.

  > no primary key, new instance is created

- The state of the given instance is then copied onto the located/newly created instance. For attributes which are present on the source instance, the value is transferred to the target instance. For mapped attributes which aren’t present on the source, the attribute is expired on the target instance, discarding its existing value.

  > copy state，原对象不存在的 attribute，目标对象会 expire and discard value

  If the `load=True` flag is left at its default, this copy process emits events and will load the target object’s unloaded collections for each attribute present on the source object, so that the incoming state can be reconciled against what’s present in the database. If `load` is passed as `False`, the incoming data is “stamped” directly without producing any history.

- The operation is cascaded to related objects and collections, as indicated by the `merge` cascade (see [Cascades](http://docs.sqlalchemy.org/en/rel_1_1/orm/cascades.html#unitofwork-cascades)).

- The new instance is returned.

With [`merge()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.merge), the given “source” instance is not modified nor is it associated with the target [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session), and remains available to be merged with any number of other [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) objects. [`merge()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.merge) is useful for taking the state of any kind of object structure without regard for its origins or current session associations and copying its state into a new session. Here’s some examples:

- An application which reads an object structure from a file and wishes to save it to the database might parse the file, build up the structure, and then use [`merge()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.merge) to save it to the database, ensuring that the data within the file is used to formulate the primary key of each element of the structure. Later, when the file has changed, the same process can be re-run, producing a slightly different object structure, which can then be `merged` in again, and the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) will automatically update the database to reflect those changes, loading each object from the database by primary key and then updating its state with the new state given.

- An application is storing objects in an in-memory cache, shared by many [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) objects simultaneously.[`merge()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.merge) is used each time an object is retrieved from the cache to create a local copy of it in each [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) which requests it. The cached object remains detached; only its state is moved into copies of itself that are local to individual [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) objects.

  In the caching use case, it’s common to use the `load=False` flag to remove the overhead of reconciling the object’s state with the database. There’s also a “bulk” version of [`merge()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.merge) called [`merge_result()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/query.html#sqlalchemy.orm.query.Query.merge_result) that was designed to work with cache-extended [`Query`](http://docs.sqlalchemy.org/en/rel_1_1/orm/query.html#sqlalchemy.orm.query.Query) objects - see the section [Dogpile Caching](http://docs.sqlalchemy.org/en/rel_1_1/orm/examples.html#examples-caching).

- An application wants to transfer the state of a series of objects into a [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) maintained by a worker thread or other concurrent system. [`merge()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.merge) makes a copy of each object to be placed into this new [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session). At the end of the operation, the parent thread/process maintains the objects it started with, and the thread/worker can proceed with local copies of those objects.

  In the “transfer between threads/processes” use case, the application may want to use the `load=False`flag as well to avoid overhead and redundant SQL queries as the data is transferred.

### Merge Tips

[`merge()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.merge) is an extremely useful method for many purposes. However, it deals with the intricate border between objects that are transient/detached and those that are persistent, as well as the automated transference of state. The wide variety of scenarios that can present themselves here often require a more careful approach to the state of objects. Common problems with merge usually involve some unexpected state regarding the object being passed to [`merge()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.merge).

Lets use the canonical example of the User and Address objects:

```python
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    addresses = relationship("Address", backref="user")

class Address(Base):
    __tablename__ = 'address'

    id = Column(Integer, primary_key=True)
    email_address = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
```

Assume a `User` object with one `Address`, already persistent:

```
>>> u1 = User(name='ed', addresses=[Address(email_address='ed@ed.com')])
>>> session.add(u1)
>>> session.commit()
```

We now create `a1`, an object outside the session, which we’d like to merge on top of the existing `Address`:

```
>>> existing_a1 = u1.addresses[0]
>>> a1 = Address(id=existing_a1.id)
```

A surprise would occur if we said this:

```python
>>> a1.user = u1
>>> a1 = session.merge(a1)
>>> session.commit()
sqlalchemy.orm.exc.FlushError: New instance <Address at 0x1298f50>
with identity key (<class '__main__.Address'>, (1,)) conflicts with
persistent instance <Address at 0x12a25d0>
```

Why is that ? We weren’t careful with our cascades. The assignment of `a1.user` to a persistent object cascaded to the backref of `User.addresses` and made our `a1` object pending, as though we had added it. Now we have*two* `Address` objects in the session:

```
>>> a1 = Address()
>>> a1.user = u1
>>> a1 in session
True
>>> existing_a1 in session
True
>>> a1 is existing_a1
False
```

Above, our `a1` is already pending in the session. The subsequent [`merge()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.merge) operation essentially does nothing. Cascade can be configured via the [`cascade`](http://docs.sqlalchemy.org/en/rel_1_1/orm/relationship_api.html#sqlalchemy.orm.relationship.params.cascade) option on [`relationship()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/relationship_api.html#sqlalchemy.orm.relationship), although in this case it would mean removing the `save-update` cascade from the `User.addresses` relationship - and usually, that behavior is extremely convenient. The solution here would usually be to not assign `a1.user` to an object already persistent in the target session.

The `cascade_backrefs=False` option of [`relationship()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/relationship_api.html#sqlalchemy.orm.relationship) will also prevent the `Address` from being added to the session via the `a1.user = u1` assignment.

Further detail on cascade operation is at [Cascades](http://docs.sqlalchemy.org/en/rel_1_1/orm/cascades.html#unitofwork-cascades).

Another example of unexpected state:

```python
>>> a1 = Address(id=existing_a1.id, user_id=u1.id)
>>> assert a1.user is None
>>> True
>>> a1 = session.merge(a1)
>>> session.commit()
sqlalchemy.exc.IntegrityError: (IntegrityError) address.user_id
may not be NULL
```

Here, we accessed a1.user, which returned its default value of `None`, which as a result of this access, has been placed in the `__dict__` of our object `a1`. Normally, this operation creates no change event, so the `user_id`attribute takes precedence during a flush. But when we merge the `Address` object into the session, the operation is equivalent to:

```
>>> existing_a1.id = existing_a1.id
>>> existing_a1.user_id = u1.id
>>> existing_a1.user = None
```

Where above, both `user_id` and `user` are assigned to, and change events are emitted for both. The `user`association takes precedence, and None is applied to `user_id`, causing a failure.

Most [`merge()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.merge) issues can be examined by first checking - is the object prematurely in the session ?

```
>>> a1 = Address(id=existing_a1, user_id=user.id)
>>> assert a1 not in session
>>> a1 = session.merge(a1)
```

Or is there state on the object that we don’t want ? Examining `__dict__` is a quick way to check:

```python
>>> a1 = Address(id=existing_a1, user_id=user.id)
>>> a1.user
>>> a1.__dict__
{'_sa_instance_state': <sqlalchemy.orm.state.InstanceState object at 0x1298d10>,
    'user_id': 1,
    'id': 1,
    'user': None}
>>> # we don't want user=None merged, remove it
>>> del a1.user
>>> a1 = session.merge(a1)
>>> # success
>>> session.commit()
```

## Expunging

Expunge removes an object from the Session, sending persistent instances to the detached state, and pending instances to the transient state:

```
session.expunge(obj1)
```

To remove all items, call [`expunge_all()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expunge_all) (this method was formerly known as `clear()`).

**remove object from session, persistent —> detached, pending  —> transient **

## Refreshing / Expiring

[Expiring](http://docs.sqlalchemy.org/en/rel_1_1/glossary.html#term-expiring) means that the database-persisted data held inside a series of object attributes is erased, in such a way that when those attributes are next accessed, a SQL query is emitted which will refresh that data from the database.

对象的属性值被擦除了，直到下次再去调用这些属性时，sqlalchemy 会发起新的查询获取这些属性值

When we talk about expiration of data we are usually talking about an object that is in the [persistent](http://docs.sqlalchemy.org/en/rel_1_1/glossary.html#term-persistent) state. For example, if we load an object as follows:

expire 只对具有 persistent 的 object 而言

```
user = session.query(User).filter_by(name='user1').first()
```

The above `User` object is persistent, and has a series of attributes present; if we were to look inside its `__dict__`, we’d see that state loaded:

```
>>> user.__dict__
{
  'id': 1, 'name': u'user1',
  '_sa_instance_state': <...>,
}
```

user.__dict__ 中能够看到属性值，他们来自数据库

where `id` and `name` refer to those columns in the database. `_sa_instance_state` is a non-database-persisted value used by SQLAlchemy internally (it refers to the [`InstanceState`](http://docs.sqlalchemy.org/en/rel_1_1/orm/internals.html#sqlalchemy.orm.state.InstanceState) for the instance. While not directly relevant to this section, if we want to get at it, we should use the [`inspect()`](http://docs.sqlalchemy.org/en/rel_1_1/core/inspection.html#sqlalchemy.inspection.inspect) function to access it).

At this point, the state in our `User` object matches that of the loaded database row. But upon expiring the object using a method such as [`Session.expire()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expire), we see that the state is removed:

```
>>> session.expire(user)
>>> user.__dict__
{'_sa_instance_state': <...>}
```

调用 expire ，属性值就会消失

We see that while the internal “state” still hangs around, the values which correspond to the `id` and `name` columns are gone. If we were to access one of these columns and are watching SQL, we’d see this:

```
>>> print(user.name)

SELECT user.id AS user_id, user.name AS user_name
FROM user
WHERE user.id = ?
(1,)
user1
```

重新获取属性值又会发起新的查询

Above, upon accessing the expired attribute `user.name`, the ORM initiated a [lazy load](http://docs.sqlalchemy.org/en/rel_1_1/glossary.html#term-lazy-load) to retrieve the most recent state from the database, by emitting a SELECT for the user row to which this user refers. Afterwards, the `__dict__` is again populated:

```
>>> user.__dict__
{
  'id': 1, 'name': u'user1',
  '_sa_instance_state': <...>,
}
```

Note

While we are peeking inside of `__dict__` in order to see a bit of what SQLAlchemy does with object attributes, we **should not modify** the contents of `__dict__` directly, at least as far as those attributes which the SQLAlchemy ORM is maintaining (other attributes outside of SQLA’s realm are fine). This is because SQLAlchemy uses [descriptors](http://docs.sqlalchemy.org/en/rel_1_1/glossary.html#term-descriptors) in order to track the changes we make to an object, and when we modify `__dict__` directly, the ORM won’t be able to track that we changed something.

Another key behavior of both [`expire()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expire) and [`refresh()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.refresh) is that all un-flushed changes on an object are discarded. That is, if we were to modify an attribute on our `User`:

```
>>> user.name = 'user2'
```

but then we call [`expire()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expire) without first calling [`flush()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.flush), our pending value of `'user2'` is discarded:

```
>>> session.expire(user)
>>> user.name
'user1'
```

expire 会放弃对属性值得修改，处于 pending 状态的 object 将会恢复原状

The [`expire()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expire) method can be used to mark as “expired” all ORM-mapped attributes for an instance:

```
# expire all ORM-mapped attributes on obj1
session.expire(obj1)
```

it can also be passed a list of string attribute names, referring to specific attributes to be marked as expired:

```
# expire only attributes obj1.attr1, obj1.attr2
session.expire(obj1, ['attr1', 'attr2'])
```

可以过期整个对象或对象的某些属性

The [`refresh()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.refresh) method has a similar interface, but instead of expiring, it emits an immediate SELECT for the object’s row immediately:

```
# reload all attributes on obj1
session.refresh(obj1)
```

与 expire 相反 refresh 是获取最新的值

[`refresh()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.refresh) also accepts a list of string attribute names, but unlike [`expire()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expire), expects at least one name to be that of a column-mapped attribute:

```
# reload obj1.attr1, obj1.attr2
session.refresh(obj1, ['attr1', 'attr2'])
```

获取某些属性的最新值

The [`Session.expire_all()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expire_all) method allows us to essentially call [`Session.expire()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expire) on all objects contained within the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) at once:

```
session.expire_all()
```

### What Actually Loads

The SELECT statement that’s emitted when an object marked with [`expire()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expire) or loaded with [`refresh()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.refresh) varies based on several factors, including:

- The load of expired attributes is triggered from **column-mapped attributes only**. While any kind of attribute can be marked as expired, including a [`relationship()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/relationship_api.html#sqlalchemy.orm.relationship) - mapped attribute, accessing an expired [`relationship()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/relationship_api.html#sqlalchemy.orm.relationship) attribute will emit a load only for that attribute, using standard relationship-oriented lazy loading. Column-oriented attributes, even if expired, will not load as part of this operation, and instead will load when any column-oriented attribute is accessed.
- [`relationship()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/relationship_api.html#sqlalchemy.orm.relationship)- mapped attributes will not load in response to expired column-based attributes being accessed.
- Regarding relationships, [`refresh()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.refresh) is more restrictive than [`expire()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expire) with regards to attributes that aren’t column-mapped. Calling [`refresh()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.refresh) and passing a list of names that only includes relationship-mapped attributes will actually raise an error. In any case, non-eager-loading [`relationship()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/relationship_api.html#sqlalchemy.orm.relationship) attributes will not be included in any refresh operation.
- [`relationship()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/relationship_api.html#sqlalchemy.orm.relationship) attributes configured as “eager loading” via the [`lazy`](http://docs.sqlalchemy.org/en/rel_1_1/orm/relationship_api.html#sqlalchemy.orm.relationship.params.lazy) parameter will load in the case of[`refresh()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.refresh), if either no attribute names are specified, or if their names are inclued in the list of attributes to be refreshed.
- Attributes that are configured as [`deferred()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/loading_columns.html#sqlalchemy.orm.deferred) will not normally load, during either the expired-attribute load or during a refresh. An unloaded attribute that’s [`deferred()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/loading_columns.html#sqlalchemy.orm.deferred) instead loads on its own when directly accessed, or if part of a “group” of deferred attributes where an unloaded attribute in that group is accessed.
- For expired attributes that are loaded on access, a joined-inheritance table mapping will emit a SELECT that typically only includes those tables for which unloaded attributes are present. The action here is sophisticated enough to load only the parent or child table, for example, if the subset of columns that were originally expired encompass only one or the other of those tables.
- When [`refresh()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.refresh) is used on a joined-inheritance table mapping, the SELECT emitted will resemble that of when [`Session.query()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.query) is used on the target object’s class. This is typically all those tables that are set up as part of the mapping.

### When to Expire or Refresh

The [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) uses the expiration feature automatically whenever the transaction referred to by the session ends. Meaning, whenever [`Session.commit()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.commit) or [`Session.rollback()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.rollback) is called, all objects within the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session)are expired, using a feature equivalent to that of the [`Session.expire_all()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expire_all) method. The rationale is that the end of a transaction is a demarcating point at which there is no more context available in order to know what the current state of the database is, as any number of other transactions may be affecting it. Only when a new transaction starts can we again have access to the current state of the database, at which point any number of changes may have occurred.

一个 session 的事务结束，也就是说 rollback 发生或者 commit 发生，expire 就会自动发生。因为上下文已经失去，没有办法知道 object 的 attrs 究竟发生了什么改变。除非下次查询开始

Transaction Isolation

Of course, most databases are capable of handling multiple transactions at once, even involving the same rows of data. When a relational database handles multiple transactions involving the same tables or rows, this is when the [isolation](http://docs.sqlalchemy.org/en/rel_1_1/glossary.html#term-isolation) aspect of the database comes into play. The isolation behavior of different databases varies considerably and even on a single database can be configured to behave in different ways (via the so-called isolation level setting). In that sense, the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) can’t fully predict when the same SELECT statement, emitted a second time, will definitely return the data we already have, or will return new data. So as a best guess, it assumes that within the scope of a transaction, unless it is known that a SQL expression has been emitted to modify a particular row, there’s no need to refresh a row unless explicitly told to do so.

事务隔离影响着属性的最新状态。session 做出的假设是在一个 transaction 中，没有办法预测 select 是返回和当前一样的数据还是最新的修改，于是除非 session 明确知道一个 sql 语句正在改变当前对象的属性，否则它不会主动刷新当前对象的属性。

The [`Session.expire()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expire) and [`Session.refresh()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.refresh)methods are used in those cases when one wants to force an object to re-load its data from the database, in those cases when it is known that the current state of data is possibly stale. Reasons for this might include:

- some SQL has been emitted within the transaction outside of the scope of the ORM’s object handling, such as if a [`Table.update()`](http://docs.sqlalchemy.org/en/rel_1_1/core/metadata.html#sqlalchemy.schema.Table.update) construct were emitted using the [`Session.execute()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.execute) method;
- if the application is attempting to acquire data that is known to have been modified in a concurrent transaction, and it is also known that the isolation rules in effect allow this data to be visible.

The second bullet has the important caveat that “it is also known that the isolation rules in effect allow this data to be visible.” This means that it cannot be assumed that an UPDATE that happened on another database connection will yet be visible here locally; in many cases, it will not. This is why if one wishes to use [`expire()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expire) or [`refresh()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.refresh) in order to view data between ongoing transactions, an understanding of the isolation behavior in effect is essential.

expire 和 refresh 方法的提供就是为了让用户可以手动实现加载最新的数据，
比如在当前事务之外有并发的事务存在可能会改变数据，或其他更新语句会改变数据，这些方法提供了总是加载
最新数据的途径。

See also

[`Session.expire()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expire)

[`Session.expire_all()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expire_all)

[`Session.refresh()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.refresh)

[isolation](http://docs.sqlalchemy.org/en/rel_1_1/glossary.html#term-isolation) - glossary explanation of isolation which includes links to Wikipedia.

[The SQLAlchemy Session In-Depth](http://techspot.zzzeek.org/2012/11/14/pycon-canada-the-sqlalchemy-session-in-depth/) - a video + slides with an in-depth discussion of the object lifecycle including the role of data expiration.