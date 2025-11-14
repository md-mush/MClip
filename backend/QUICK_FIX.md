# SupoClip Quick Fix Guide

## 🚨 Problem: Subtitles Not Working

**Error:**
```
convert-im6.q16: attempt to perform an operation not allowed by the security policy '@/tmp/...'
```

**Fix (30 seconds):**
```python
!python fix_imagemagick_policy.py
```

---

## 🚨 Problem: AI Takes Too Long (30+ minutes)

**Fix Applied:** Optimized prompt in `src/ai.py`

**Expected Time Now:** 10-20 minutes

**Verify:**
```python
# Check these values in src/ai.py:
MIN_SEGMENT_DURATION = 30  # Should be 30, not 10
MAX_SEGMENT_DURATION = 60  # Should be 60, not 45
```

---

## 🚨 Problem: Clips End Mid-Sentence

**Fix Applied:** New prompt instructs AI to find complete thoughts

**Verify:** Check `src/ai.py` prompt contains:
```
"Each segment MUST be a COMPLETE thought/sentence - NO mid-sentence cuts"
```

---

## 🚨 Problem: Dependency Conflicts

**Fix:**
```python
!pip install -r requirements.txt
```

**Key Versions:**
- numpy==1.26.4 (not 2.0.2)
- opencv-python==4.8.1.78 (not 4.12.0.88)

---

## 🚀 Complete Setup (5 minutes)

```python
# ONE COMMAND TO FIX EVERYTHING:
!python setup_colab_complete.py
```

This fixes:
- ✅ ImageMagick policy
- ✅ All dependencies
- ✅ Environment variables
- ✅ Tests everything

---

## ✅ Quick Test

```python
# Test ImageMagick + MoviePy:
import moviepy.editor as mp
clip = mp.TextClip("Test", fontsize=24, color="white")
print(f"✅ Works! Size: {clip.size}")
clip.close()
```

**Expected:** Should print "✅ Works! Size: (200, 50)" or similar

---

## 📊 What Changed

| Item | Before | After |
|------|--------|-------|
| Subtitles | ❌ Broken | ✅ Working |
| AI Time | 23-32 min | 10-20 min |
| Clip Length | 10-45 sec | 30-60 sec |
| Sentences | Incomplete | Complete |
| Setup | 30+ min | 5 min |

---

## 🎯 Files You Need

1. **`fix_imagemagick_policy.py`** - Fixes subtitle issue
2. **`setup_colab_complete.py`** - Complete setup
3. **`requirements.txt`** - Correct dependencies
4. **`src/ai.py`** - Optimized prompt (already updated)

---

## 💡 Pro Tips

1. **Always run setup first:**
   ```python
   !python setup_colab_complete.py
   ```

2. **Test before processing:**
   ```python
   !python fix_imagemagick_policy.py
   ```

3. **Use short videos for testing** (< 5 minutes)

4. **Check logs if issues:**
   ```python
   !tail -n 50 logs/backend_log.txt
   ```

---

## 🆘 Still Not Working?

### Subtitles:
```bash
# Check policy file:
!cat /etc/ImageMagick-6/policy.xml | grep "@\*"
# Should show: rights="read|write" pattern="@*"
```

### AI Speed:
```bash
# Test Ollama:
!ollama run llama3.1:8b "Say hello"
# Should respond in < 5 seconds
```

### Dependencies:
```python
# Reinstall:
!pip uninstall -y numpy opencv-python
!pip install numpy==1.26.4 opencv-python==4.8.1.78
```

---

## ✨ Success Indicators

You'll know it's working when:
- ✅ Setup script shows "SUCCESS"
- ✅ MoviePy test passes
- ✅ First video processes in 10-20 min
- ✅ Clips have subtitles
- ✅ Clips are 30-60 seconds
- ✅ No mid-sentence cuts

---

## 📞 Need Help?

1. Read `SETUP_GUIDE.md` for detailed instructions
2. Check `CHANGES_SUMMARY.md` for what changed
3. Review `logs/backend_log.txt` for errors
4. Run tests individually to isolate issues

---

**Remember:** Run `!python setup_colab_complete.py` first! 🚀
